from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class Dataset(BaseModel):
    name: str = Field(description="数据集名称")
    size: str = Field(description="数据集规模")
    source: str = Field(description="数据集来源")


class Baseline(BaseModel):
    name: str = Field(description="对比方法名称")
    source: str = Field(description="来源文献")
    code_url: str = Field(description="代码链接")


class ExperimentResult(BaseModel):
    objectives: List[str] = Field(description="实验目标列表")
    datasets: List[Dataset] = Field(description="数据集列表")
    metrics: Dict[str, str] = Field(description="评估指标，键值对形式")
    baselines: List[Baseline] = Field(description="对比方法列表")
    procedures: List[str] = Field(description="实验步骤列表")
    expected_outcomes: List[str] = Field(description="预期结果列表")


class ExperimentAgent:
    def __init__(self, cached_llm=None):
        self._validate_api_key()
        self.llm = cached_llm or get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=ExperimentResult)
    
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
    
    def design_experiment(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """设计实验方案"""
        logger.info("Designing experiment")
        
        solution_text = str(solution)
        
        format_instructions = self.parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的实验设计专家。你的任务是根据解决方案设计完整的实验方案。
            {format_instructions}
            IMPORTANT: Output ONLY the valid JSON object, without any additional text, markdown code blocks, or explanations."""),
            ("human", """解决方案：
{solution_text}

请设计实验方案。""")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result: ExperimentResult = chain.invoke({
                "format_instructions": format_instructions,
                "solution_text": solution_text
            })
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error designing experiment: {str(e)}")
            return {
                "objectives": [],
                "datasets": [],
                "metrics": {},
                "baselines": [],
                "procedures": [],
                "expected_outcomes": []
            }
    
    def generate_experiment_report(self, solution: Dict[str, Any] = None,
                                     experiment: Dict[str, Any] = None) -> str:
        """生成实验设计报告（Markdown格式）

        experiment: 如果已调用过 design_experiment，直接传入结果，避免重复 LLM 调用
        """
        logger.info("Generating experiment report")
        if experiment is None:
            experiment = self.design_experiment(solution or {})
        
        md = "# 实验设计\n\n"
        
        # 实验目标
        md += "## 一、实验目标\n\n"
        for i, objective in enumerate(experiment.get("objectives", []), 1):
            md += f"{i}. {objective}\n"
        
        # 数据集
        md += "\n## 二、实验设置\n\n"
        md += "### 数据集\n"
        md += "| 数据集 | 规模 | 来源 |\n"
        md += "|--------|------|------|\n"
        for dataset in experiment.get("datasets", []):
            md += f"| {dataset.get('name', '')} | {dataset.get('size', '')} | {dataset.get('source', '')} |\n"
        
        # 评估指标
        md += "\n### 评估指标\n"
        md += "| 指标 | 计算方式 |\n"
        md += "|------|----------|\n"
        for key, value in experiment.get("metrics", {}).items():
            md += f"| {key} | {value} |\n"
        
        # 实验步骤
        md += "\n## 三、实验步骤\n\n"
        for i, procedure in enumerate(experiment.get("procedures", []), 1):
            md += f"{i}. {procedure}\n"
        
        # 对比方法
        md += "\n## 四、对比方法\n\n"
        md += "| 方法 | 来源 | 代码链接 |\n"
        md += "|------|------|----------|\n"
        for baseline in experiment.get("baselines", []):
            code_url = baseline.get("code_url", "N/A")
            md += f"| {baseline.get('name', '')} | {baseline.get('source', '')} | [{code_url}]({code_url}) |\n"
        
        # 预期结果
        md += "\n## 五、预期结果\n\n"
        for outcome in experiment.get("expected_outcomes", []):
            md += f"- {outcome}\n"
        
        return md
