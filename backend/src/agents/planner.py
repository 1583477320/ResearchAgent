from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
import re
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class ResearchPlan(BaseModel):
    overview: str = Field(description="研究领域的简要概述")
    keywords: List[str] = Field(description="用于搜索论文的关键词列表")
    subtopics: List[str] = Field(description="建议探索的子主题列表")


class PlannerAgent:
    def __init__(self, cached_llm=None):
        self._validate_api_key()
        self.llm = cached_llm or get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=ResearchPlan)

    def _validate_api_key(self):
        provider = settings.llm_provider.lower()
        if provider == "deepseek":
            if not settings.deepseek_api_key or settings.deepseek_api_key == "your_deepseek_api_key":
                raise ValueError("DeepSeek API key not configured...")
        else:
            if not settings.llm_api_key or settings.llm_api_key == "your_qwen_api_key":
                raise ValueError("Qwen API key not configured...")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValueError, Exception)),
        reraise=True
    )
    def plan_research(self, topic: str) -> Dict[str, Any]:
        logger.info(f"Planning research for topic: {topic}")

        # 获取格式指令
        format_instructions = self.parser.get_format_instructions()

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research planner. Your task is to analyze a research topic and create a comprehensive research plan.

{format_instructions}

IMPORTANT: Output ONLY the valid JSON object, without any additional text, markdown code blocks, or explanations."""),
            ("human", "Research Topic: {topic}")
        ])

        # 链式调用：prompt -> llm -> parser
        chain = prompt | self.llm | self.parser

        try:
            plan_obj: ResearchPlan = chain.invoke({
                "topic": topic,
                "format_instructions": format_instructions
            })
            logger.info(f"Research plan generated successfully: {plan_obj.keywords}")
            return plan_obj.model_dump()
        except Exception as e:
            logger.error(f"Failed to generate research plan: {str(e)}")
            # 可选：记录原始响应以便调试
            raise ValueError(f"Failed to generate research plan: {str(e)}")