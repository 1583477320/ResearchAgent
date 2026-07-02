from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CriticFeedback(BaseModel):
    valid_gaps: List[Dict[str, Any]] = Field(description="经过验证的有效研究空白")
    invalid_gaps: List[Dict[str, Any]] = Field(description="无效或不合理的研究空白")
    suggestions: List[str] = Field(description="改进建议")
    confidence: int = Field(description="整体置信度（1-5）")


class CriticAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=CriticFeedback)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
你是一位专业的学术评审专家。你的任务是对研究空白分析结果进行严格审查。

审查标准：
1. 研究空白是否真实存在，是否已有相关研究解决
2. 问题定义是否清晰明确
3. 研究空白的重要性和可行性评估是否合理
4. 是否超出当前领域范围

请输出验证结果和改进建议。
"""),
            ("human", """
研究主题：{topic}

论文列表：
{papers}

当前gap分析结果：
{gap_analysis}

请对上述gap分析进行审查，输出格式：
{format_instructions}
""")
        ])
    
    def review_gaps(self, topic: str, papers: str, gap_analysis: str) -> CriticFeedback:
        """审查研究空白分析结果"""
        logger.info("Reviewing gap analysis")
        
        chain = self.prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "topic": topic,
                "papers": papers,
                "gap_analysis": gap_analysis,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Error reviewing gaps: {str(e)}")
            return CriticFeedback(
                valid_gaps=[],
                invalid_gaps=[],
                suggestions=["审查过程中发生错误"],
                confidence=1
            )
