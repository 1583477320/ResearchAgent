from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class SolvedProblem(BaseModel):
    problem: str = Field(description="已解决的问题")
    solution: str = Field(description="解决方案")
    representative_work: str = Field(description="代表性工作")


class ResearchGap(BaseModel):
    description: str = Field(description="研究空白描述")
    importance: int = Field(description="重要性评分，1-5分")
    feasibility: int = Field(description="可行性评分，1-5分")
    potential_value: str = Field(description="潜在价值")


class ResearchQuestion(BaseModel):
    question: str = Field(description="研究问题")
    background: str = Field(description="背景说明")
    importance: int = Field(description="重要性评分，1-5分")
    assumptions: List[str] = Field(description="研究假设列表")


class GapAnalysisResult(BaseModel):
    solved_problems: List[SolvedProblem] = Field(description="已解决的问题列表")
    research_gaps: List[ResearchGap] = Field(description="研究空白列表")
    research_questions: List[ResearchQuestion] = Field(description="研究问题列表")


class GapAgent:
    def __init__(self):
        self._validate_api_key()
        self.llm = get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=GapAnalysisResult)
    
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
    
    def identify_gaps(self, papers_analysis: List[Dict[str, Any]], classification: Dict[str, Any], 
                       critic_feedback: Dict[str, Any] = None) -> Dict[str, Any]:
        """识别研究空白"""
        logger.info("Identifying research gaps")
        
        analysis_text = "\n\n".join([
            f"论文: {analysis.get('title', '')}\n问题: {analysis.get('problem', '')}\n方法: {analysis.get('method', '')}\n局限: {analysis.get('limitation', '')}"
            for analysis in papers_analysis
        ])
        
        classification_text = str(classification)
        
        feedback_text = ""
        if critic_feedback:
            invalid_gaps = critic_feedback.get("invalid_gaps", [])
            suggestions = critic_feedback.get("suggestions", [])
            
            if invalid_gaps:
                feedback_text += "\n之前分析被指出的无效空白：\n"
                for gap in invalid_gaps[:3]:
                    feedback_text += f"- {gap.get('description', '')}\n"
            
            if suggestions:
                feedback_text += "\n改进建议：\n"
                for suggestion in suggestions[:5]:
                    feedback_text += f"- {suggestion}\n"
        
        format_instructions = self.parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的研究空白分析专家。你的任务是分析现有研究，发现研究空白并提出研究问题。
            {format_instructions}
            IMPORTANT: Output ONLY the valid JSON object, without any additional text, markdown code blocks, or explanations."""),
            ("human", """论文分析结果：
{analysis_text}

分类数据：
{classification_text}

{feedback_text}

请分析研究空白并提出研究问题。注意：如果有之前的审查反馈，请根据反馈改进分析。""")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result: GapAnalysisResult = chain.invoke({
                "format_instructions": format_instructions,
                "analysis_text": analysis_text,
                "classification_text": classification_text,
                "feedback_text": feedback_text
            })
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error identifying research gaps: {str(e)}")
            return {
                "solved_problems": [],
                "research_gaps": [],
                "research_questions": []
            }
    
    def generate_gap_report(self, papers_analysis: List[Dict[str, Any]], classification: Dict[str, Any]) -> str:
        """生成研究空白报告（Markdown格式）"""
        logger.info("Generating gap report")
        
        gaps_data = self.identify_gaps(papers_analysis, classification)
        
        md = "# 研究空白报告\n\n"
        
        # 已解决问题
        md += "## 一、已解决问题\n\n"
        if gaps_data.get("solved_problems"):
            md += "| 问题 | 解决方案 | 代表性工作 |\n"
            md += "|------|----------|------------|\n"
            for problem in gaps_data["solved_problems"]:
                md += f"| {problem.get('problem', '')} | {problem.get('solution', '')} | {problem.get('representative_work', '')} |\n"
        else:
            md += "暂无已解决问题分析。\n\n"
        
        # 研究空白
        md += "## 二、研究空白\n\n"
        for i, gap in enumerate(gaps_data.get("research_gaps", []), 1):
            md += f"### 空白{i}：{gap.get('description', '')}\n"
            md += f"- **重要性**：{'★' * gap.get('importance', 0)}\n"
            md += f"- **可行性**：{'★' * gap.get('feasibility', 0)}\n"
            md += f"- **潜在价值**：{gap.get('potential_value', '')}\n\n"
        
        # 研究机会评估
        md += "## 三、研究机会评估\n\n"
        md += "| 机会 | 可行性 | 价值 | 风险 |\n"
        md += "|------|--------|------|------|\n"
        for gap in gaps_data.get("research_gaps", []):
            importance = gap.get("importance", 3)
            feasibility = gap.get("feasibility", 3)
            md += f"| {gap.get('description', '')[:30]}... | {'高' if feasibility >= 4 else '中' if feasibility >= 2 else '低'} | {'高' if importance >= 4 else '中' if importance >= 2 else '低'} | 中 |\n"
        
        return md
    
    def generate_research_questions(self, papers_analysis: List[Dict[str, Any]], classification: Dict[str, Any]) -> str:
        """生成研究问题（Markdown格式）"""
        logger.info("Generating research questions")
        
        gaps_data = self.identify_gaps(papers_analysis, classification)
        
        md = "# 研究问题\n\n"
        
        # 核心问题
        md += "## 一、核心问题\n\n"
        for i, question in enumerate(gaps_data.get("research_questions", []), 1):
            md += f"### Q{i}：{question.get('question', '')}\n"
            md += f"- **背景**：{question.get('background', '')}\n"
            md += f"- **重要性**：{'★' * question.get('importance', 0)}\n"
            md += f"- **研究假设**：\n"
            for j, assumption in enumerate(question.get('assumptions', []), 1):
                md += f"  {j}. {assumption}\n"
            md += "\n"
        
        # 子问题
        md += "## 二、子问题\n\n"
        md += "根据核心问题，可以进一步分解为以下子问题：\n"
        for i, question in enumerate(gaps_data.get("research_questions", []), 1):
            md += f"- Q{i}.1：如何量化评估{question.get('question', '')[:20]}？\n"
            md += f"- Q{i}.2：{question.get('question', '')[:20]}的边界条件是什么？\n"
        
        return md
