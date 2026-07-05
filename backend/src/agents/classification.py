from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
from src.schemas.paper import Paper
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class Category(BaseModel):
    name: str = Field(description="类别名称")
    description: str = Field(description="类别描述")
    papers: List[str] = Field(description="该类别下的论文标题列表")


class HotTopic(BaseModel):
    topic: str = Field(description="热点主题")
    popularity: int = Field(description="热度评分，1-5分")
    representative_papers: List[str] = Field(description="代表性论文标题列表")


class ClassificationResult(BaseModel):
    categories: List[Category] = Field(description="分类列表")
    hierarchy: Dict[str, Any] = Field(description="研究领域层次结构")
    hot_topics: List[HotTopic] = Field(description="研究热点列表")


class ClassificationAgent:
    def __init__(self, cached_llm=None):
        self._validate_api_key()
        self.llm = cached_llm or get_llm_client()
        self.parser = PydanticOutputParser(pydantic_object=ClassificationResult)
    
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
    
    def classify_papers(self, papers: List[Paper]) -> Dict[str, Any]:
        """对论文进行分类"""
        logger.info(f"Classifying {len(papers)} papers")
        
        papers_text = "\n\n".join([
            f"论文 {i+1}:\n标题: {paper.title}\n作者: {', '.join(paper.authors)}\n摘要: {paper.abstract}"
            for i, paper in enumerate(papers)
        ])
        
        format_instructions = self.parser.get_format_instructions()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的学术分类专家。你的任务是对论文进行分类，构建研究领域地图。
            {format_instructions}
            IMPORTANT: Output ONLY the valid JSON object, without any additional text, markdown code blocks, or explanations."""),
            ("human", f"""论文列表：
{papers_text}

请对上述论文进行分类并构建研究领域地图。输出格式应包含categories、hierarchy和hot_topics字段。""")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result: ClassificationResult = chain.invoke({
                "format_instructions": format_instructions
            })
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error classifying papers: {str(e)}")
            return {
                "categories": [],
                "hierarchy": {"level1": [], "level2": {}},
                "hot_topics": []
            }
    
    def _format_hierarchy(self, hierarchy: Dict[str, Any], indent: int = 0) -> str:
        """递归格式化层次结构为ASCII图"""
        lines = []
        keys = list(hierarchy.keys())
        
        for i, key in enumerate(keys):
            prefix = "│   " * (indent - 1) if indent > 0 else ""
            if indent > 0:
                prefix += "└── " if i == len(keys) - 1 else "├── "
            
            lines.append(f"{prefix}{key}")
            
            if isinstance(hierarchy[key], dict):
                lines.append(self._format_hierarchy(hierarchy[key], indent + 1))
        
        return "\n".join(lines)
    
    def build_research_map(self, papers: List[Paper]) -> str:
        """构建研究领域地图（Markdown格式）"""
        logger.info("Building research map")
        
        classification = self.classify_papers(papers)
        
        # 生成研究地图 Markdown
        md = "# 研究领域地图\n\n"
        
        # 领域架构
        md += "## 一、领域架构\n\n"
        hierarchy = classification.get("hierarchy", {})
        if hierarchy:
            md += "```\n"
            md += self._format_hierarchy(hierarchy)
            md += "\n```\n\n"
        else:
            md += "当前研究领域的架构分析待补充。\n\n"
        
        # 研究热点
        md += "## 二、研究热点\n\n"
        md += "| 主题 | 热度 | 代表论文 |\n"
        md += "|------|------|----------|\n"
        for topic in classification.get("hot_topics", []):
            papers_list = ", ".join(topic.get("representative_papers", []))[:50]
            popularity = topic.get("popularity", 0)
            md += f"| {topic.get('topic', '')} | {'★' * popularity} | {papers_list} |\n"
        
        # 发展趋势
        md += "\n## 三、发展趋势\n\n"
        md += "### 时间线\n"
        md += "- 当前研究主要集中在以下方向：\n"
        for cat in classification.get("categories", []):
            md += f"- **{cat.get('name', '')}**: {cat.get('description', '')}\n"
        
        return md
    
    def generate_paper_table_json(self, papers: List[Paper]) -> str:
        """生成论文对比表格（JSON格式），供后续智能体分析使用"""
        logger.info("Generating paper table JSON")
        
        papers_data = []
        for i, paper in enumerate(papers):
            paper_entry = {
                "id": f"paper_{str(i+1).zfill(3)}",
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.publication_date,
                "source": paper.source,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "abstract": paper.abstract,
                "method": "",
                "dataset": "",
                "limitation": "",
                "contribution": ""
            }
            papers_data.append(paper_entry)
        
        result = {
            "papers": papers_data,
            "metadata": {
                "total_papers": len(papers),
                "fields": [
                    "id", "title", "authors", "year", "source", "url", 
                    "pdf_url", "abstract", "method", "dataset", "limitation", "contribution"
                ]
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
