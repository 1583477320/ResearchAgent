from typing import List, Dict, Any
from langchain.schema.output_parser import StrOutputParser
from src.schemas.paper import Paper
from src.utils.llm_client import get_llm_client
from src.utils.prompts import AgentPrompts
from src.utils.logger import get_logger
from src.utils.config import settings
import json

logger = get_logger(__name__)


class WriterAgent:
    def __init__(self):
        self._validate_api_key()
        self.llm = get_llm_client()
        self.prompt = AgentPrompts.WRITER
    
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
    
    def generate_final_report(self, topic: str, 
                              gap_report: str = "", research_questions: str = "", 
                              solution: str = "", experiment_design: str = "") -> str:
        """生成最终报告"""
        logger.info(f"Generating final report for topic: {topic}")
        
        chain = self.prompt | self.llm | StrOutputParser()
        
        try:
            report = chain.invoke({
                "topic": topic,
                "gap_report": gap_report,
                "research_questions": research_questions,
                "solution": solution,
                "experiment_design": experiment_design
            })
            return report
        except Exception as e:
            logger.error(f"Error generating final report: {str(e)}")
            return f"# 研究报告：{topic}\n\n报告生成失败，请重试。"
    
    def generate_research_package(self, topic: str, papers: List[Paper], 
                                   gap_data: Dict[str, Any] = None,
                                   solution_data: Dict[str, Any] = None,
                                   experiment_data: Dict[str, Any] = None,
                                   paper_table_json: str = "") -> Dict[str, str]:
        """生成完整的研究包"""
        logger.info(f"Generating research package for topic: {topic}")
        
        package = {}
        
        # 0. papers_table.json - 论文对比表格（供后续智能体分析使用）
        if paper_table_json:
            package["papers_table.json"] = paper_table_json
        else:
            papers_data = []
            for i, paper in enumerate(papers):
                papers_data.append({
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
                })
            package["papers_table.json"] = json.dumps({
                "papers": papers_data,
                "metadata": {"total_papers": len(papers)}
            }, ensure_ascii=False, indent=2)
        
        # 1. gap_report.md
        package["gap_report.md"] = gap_report = self._generate_gap_report(gap_data)
        
        # 2. research_questions.md
        package["research_questions.md"] = research_questions = self._generate_research_questions(gap_data)
        
        # 3. solution.md
        package["solution.md"] = solution = self._generate_solution(solution_data)
        
        # 4. experiment_design.md
        package["experiment_design.md"] = experiment_design = self._generate_experiment_design(experiment_data)
        
        # 5. final_report.md
        package["final_report.md"] = self.generate_final_report(
            topic=topic,
            gap_report=gap_report,
            research_questions=research_questions,
            solution=solution,
            experiment_design=experiment_design
        )
        
        logger.info("Research package generated successfully")
        return package
    
    def _generate_research_map(self, classification_data: Dict[str, Any]) -> str:
        """生成研究地图"""
        if not classification_data:
            return "# 研究领域地图\n\n暂无数据"
        
        md = "# 研究领域地图\n\n"
        md += "## 一、领域架构\n\n"
        md += "当前研究领域的架构分析待补充。\n\n"
        md += "## 二、研究热点\n\n"
        for topic in classification_data.get("hot_topics", []):
            md += f"- **{topic.get('topic', '')}**\n"
        return md
    
    def _generate_gap_report(self, gap_data: Dict[str, Any]) -> str:
        """生成研究空白报告"""
        if not gap_data:
            return "# 研究空白报告\n\n暂无数据"
        
        md = "# 研究空白报告\n\n"
        md += "## 一、已解决问题\n\n"
        for problem in gap_data.get("solved_problems", []):
            md += f"- {problem.get('problem', '')}\n"
        md += "\n## 二、研究空白\n\n"
        for gap in gap_data.get("research_gaps", []):
            md += f"- {gap.get('description', '')}\n"
        return md
    
    def _generate_research_questions(self, gap_data: Dict[str, Any]) -> str:
        """生成研究问题"""
        if not gap_data:
            return "# 研究问题\n\n暂无数据"
        
        md = "# 研究问题\n\n"
        md += "## 一、核心问题\n\n"
        for question in gap_data.get("research_questions", []):
            md += f"- {question.get('question', '')}\n"
        return md
    
    def _generate_solution(self, solution_data: Dict[str, Any]) -> str:
        """生成解决方案"""
        if not solution_data:
            return "# 解决方案\n\n暂无数据"
        
        md = "# 解决方案\n\n"
        md += f"## 一、核心思路\n{solution_data.get('approach', '')}\n\n"
        md += "## 二、创新点\n\n"
        for point in solution_data.get("innovation_points", []):
            md += f"- {point}\n"
        return md
    
    def _generate_experiment_design(self, experiment_data: Dict[str, Any]) -> str:
        """生成实验设计"""
        if not experiment_data:
            return "# 实验设计\n\n暂无数据"
        
        md = "# 实验设计\n\n"
        md += "## 一、实验目标\n\n"
        for objective in experiment_data.get("objectives", []):
            md += f"- {objective}\n"
        md += "\n## 二、数据集\n\n"
        for dataset in experiment_data.get("datasets", []):
            md += f"- {dataset.get('name', '')}\n"
        return md
