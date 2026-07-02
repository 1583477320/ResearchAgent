from typing import Optional
from langchain_openai import ChatOpenAI
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
) -> ChatOpenAI:
    provider = provider or settings.llm_provider
    
    if provider.lower() == "deepseek":
        api_key = api_key or settings.deepseek_api_key
        base_url = base_url or settings.deepseek_api_base_url
        model_name = model_name or settings.deepseek_model_name
    else:
        api_key = api_key or settings.llm_api_key
        base_url = base_url or settings.llm_api_base_url
        model_name = model_name or settings.llm_model_name
    
    logger.info(f"Initializing LLM client with provider: {provider}, model: {model_name}")
    
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7
    )
