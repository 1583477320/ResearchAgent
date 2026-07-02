from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class SolutionResult(BaseModel):
    approach: str = Field(description="解决方案的核心思路")
    methodology: str = Field(description="方法论")
    innovation_points: List[str] = Field(description="创新点列表")
    expected_results: Dict[str, str] = Field(description="预期结果，键值对形式")
    implementation_plan: List[str] = Field(description="实施计划步骤列表")


class SolutionAgent:
    def __init__(self):
        self._validate_api_key()
        self.llm = get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=SolutionResult)
    
    def _validate_api_key(self):
        provider = settings.llm_provider.lower()
        
        if provider == "deepseek":
            if not settings.deepseek_api_key or settings.deepseek_api_key == "your_deepseek_api_key":
                raise ValueError(
                    "DeepSeek API key is not configured. Please set the DEEPSEEK_API_KEY environment variable in the .env file.\n"
                    "Example: DEEPSEEK_API_KEY=your_actual_api_key"
                )
        else:
            if not settings.llm_api_key or settings.llm_api_key == "your_qwen_api_key":
                raise ValueError(
                    "Qwen API key is not configured. Please set the LLM_API_KEY environment variable in the .env file.\n"
                    "Example: LLM_API_KEY=your_actual_api_key"
                )
    
    def propose_solution(self, research_gaps: List[Dict[str, Any]], research_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提出解决方案"""
        logger.info("Proposing solutions")
        
        gaps_text = "\n\n".join([
            f"空白{i+1}: {gap.get('description', '')}"
            for i, gap in enumerate(research_gaps)
        ])
        
        questions_text = "\n\n".join([
            f"问题{i+1}: {question.get('question', '')}"
            for i, question in enumerate(research_questions)
        ])
        
        format_instructions = self.parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的解决方案专家。你的任务是根据研究空白和研究问题提出创新的解决方案。
            {format_instructions}
            IMPORTANT: Output ONLY the valid JSON object, without any additional text, markdown code blocks, or explanations."""),
            ("human", """研究空白：
{gaps_text}

研究问题：
{questions_text}

请提出解决方案。""")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result: SolutionResult = chain.invoke({
                "format_instructions": format_instructions,
                "gaps_text": gaps_text,
                "questions_text": questions_text
            })
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error proposing solution: {str(e)}")
            return {
                "approach": "",
                "methodology": "",
                "innovation_points": [],
                "expected_results": {},
                "implementation_plan": []
            }
    
    def generate_solution_report(self, research_gaps: List[Dict[str, Any]], research_questions: List[Dict[str, Any]]) -> str:
        """生成解决方案报告（Markdown格式）"""
        logger.info("Generating solution report")
        
        solution = self.propose_solution(research_gaps, research_questions)
        
        md = "# 解决方案\n\n"
        
        # 方案概述
        md += "## 一、方案概述\n\n"
        md += f"### 核心思路\n{solution.get('approach', '')}\n\n"
        md += f"### 方法论\n{solution.get('methodology', '')}\n\n"
        
        # 创新点
        md += "## 二、创新点\n\n"
        for i, point in enumerate(solution.get("innovation_points", []), 1):
            md += f"{i}. **{point}**\n\n"
        
        # 预期效果
        md += "## 三、预期效果\n\n"
        md += "| 指标 | 预期值 | 对比基准 |\n"
        md += "|------|--------|----------|\n"
        for key, value in solution.get("expected_results", {}).items():
            md += f"| {key} | {value} | 现有方法 |\n"
        
        # 实施计划
        md += "\n## 四、实施计划\n\n"
        for i, step in enumerate(solution.get("implementation_plan", []), 1):
            md += f"{i}. {step}\n"
        
        return md
