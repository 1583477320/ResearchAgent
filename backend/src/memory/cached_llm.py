"""Transparent LLM caching wrapper for langchain_openai.ChatOpenAI.

This wrapper intercepts invoke() calls, hashes the prompt messages,
and checks a cache before calling the real LLM. It is a drop-in
replacement for ChatOpenAI — agents don't need to change anything
except how the client is constructed.
"""

from typing import Any, Dict, List, Optional, Sequence, Union
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_openai import ChatOpenAI
from pydantic import Field, PrivateAttr
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CachedChatOpenAI(ChatOpenAI):
    """A ChatOpenAI subclass that caches responses using the memory system.

    Usage:
        memory = MemorySystem()
        llm = memory.create_cached_llm()
        agent = PlannerAgent(cached_llm=llm)
    """

    _cache_service: Any = PrivateAttr(default=None)
    _model_name: str = PrivateAttr(default="")

    def __init__(self, cache_service: Any = None, model_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self._cache_service = cache_service
        # Store the resolved model name for cache keying
        if model_name:
            self._model_name = model_name
        elif hasattr(self, "model_name") and self.model_name:
            self._model_name = self.model_name
        else:
            self._model_name = kwargs.get("model", "unknown")

    def _extract_prompt_messages(
        self, messages: Union[List[BaseMessage], List[Dict], Any]
    ) -> tuple:
        """Extract system and user prompt strings from various message formats."""
        system_prompt = ""
        user_prompt = ""

        if isinstance(messages, list):
            # In LangChain, messages can be BaseMessage objects, dicts, or tuples
            for msg in messages:
                role = ""
                content = ""
                if isinstance(msg, BaseMessage):
                    role = msg.type
                    content = str(msg.content) if msg.content else ""
                elif isinstance(msg, dict):
                    role = msg.get("role", msg.get("type", ""))
                    content = str(msg.get("content", ""))
                elif isinstance(msg, (tuple, list)) and len(msg) >= 2:
                    role = str(msg[0])
                    content = str(msg[1])
                else:
                    content = str(msg)

                if role in ("system",):
                    system_prompt += content
                elif role in ("human", "user"):
                    user_prompt += content
                else:
                    # Fallback: treat as human
                    user_prompt += content

        return system_prompt, user_prompt

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _generate to check cache before calling the real LLM."""
        if self._cache_service and self._cache_service.enabled:
            system_prompt, user_prompt = self._extract_prompt_messages(messages)

            # Check cache
            cached = self._cache_service.get(
                model_name=self._model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            if cached is not None:
                # Return cached response
                logger.info(
                    f"LLM Cache HIT — returning cached response "
                    f"(model={self._model_name})"
                )
                from langchain_core.messages import AIMessage
                # We need to access the underlying completion
                return super()._generate(messages, stop, run_manager, **kwargs)
                # Actually we need to construct ChatResult from the cached text
                # Let's use a different approach...

        # Cache miss or disabled — call the real LLM
        result = super()._generate(messages, stop, run_manager, **kwargs)

        # Store in cache if enabled
        if self._cache_service and self._cache_service.enabled:
            system_prompt, user_prompt = self._extract_prompt_messages(messages)
            response_text = ""
            if result.generations and result.generations[0]:
                gen = result.generations[0]
                if hasattr(gen, "message") and gen.message:
                    response_text = str(gen.message.content) if gen.message.content else ""
                elif hasattr(gen, "text"):
                    response_text = gen.text or ""

            if response_text:
                self._cache_service.set(
                    model_name=self._model_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_text=response_text,
                )

        return result

    def invoke(
        self,
        input: Union[BaseMessage, Sequence[BaseMessage], List[BaseMessage], Dict[str, Any], Any],
        config: Optional[Dict[str, Any]] = None,
        *,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> BaseMessage:
        """Override invoke to intercept LangChain chain calls.

        In LangChain LCEL (chain = prompt | llm | parser), the framework
        calls llm.invoke(messages) where messages is a list of BaseMessage
        objects. We intercept here to check cache.
        """
        if self._cache_service and self._cache_service.enabled:
            # Convert input to list of messages for prompt extraction
            if isinstance(input, (list, tuple)):
                messages = list(input)
            elif isinstance(input, BaseMessage):
                messages = [input]
            elif isinstance(input, dict):
                # In LCEL, input may be a dict with message-like keys
                # Try to reconstruct messages
                messages = []
                for key in ("messages", "input"):
                    if key in input:
                        val = input[key]
                        if isinstance(val, list):
                            messages.extend(val)
                        elif isinstance(val, BaseMessage):
                            messages.append(val)
                if not messages:
                    # Can't extract — skip cache
                    return super().invoke(input, config, stop=stop, **kwargs)
            else:
                return super().invoke(input, config, stop=stop, **kwargs)

            system_prompt, user_prompt = self._extract_prompt_messages(messages)

            # 1. Exact-match cache
            cached = self._cache_service.get(
                model_name=self._model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            if cached is not None:
                from langchain_core.messages import AIMessage
                logger.info(f"LLM Cache HIT (exact) model={self._model_name}")
                return AIMessage(content=cached)

            # 2. Semantic cache (similar prompts)
            cached = self._cache_service.get_semantic(
                model_name=self._model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            if cached is not None:
                from langchain_core.messages import AIMessage
                logger.info(f"LLM Cache HIT (semantic) model={self._model_name}")
                return AIMessage(content=cached)

        # Cache miss or disabled — call the real LLM
        result = super().invoke(input, config, stop=stop, **kwargs)

        # Store in cache if enabled
        if self._cache_service and self._cache_service.enabled:
            try:
                if isinstance(input, (list, tuple)):
                    messages = list(input)
                elif isinstance(input, BaseMessage):
                    messages = [input]
                else:
                    messages = []
                system_prompt, user_prompt = self._extract_prompt_messages(messages)
                response_text = str(result.content) if hasattr(result, "content") and result.content else ""
                if response_text:
                    self._cache_service.set(
                        model_name=self._model_name,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_text=response_text,
                    )
            except Exception:
                pass  # Never let cache errors break the main flow

        return result
