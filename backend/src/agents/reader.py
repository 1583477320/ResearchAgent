from typing import List, Dict, Any
from langchain.schema.output_parser import StrOutputParser
from src.schemas.paper import Paper
from src.utils.llm_client import get_llm_client
from src.utils.prompts import AgentPrompts
from src.utils.logger import get_logger
from src.utils.config import settings
import json

logger = get_logger(__name__)


class ReadingAgent:
    def __init__(self, cached_llm=None):
        self._validate_api_key()
        self.llm = cached_llm or get_llm_client()
        self.prompt = AgentPrompts.READER
    
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
    
    def analyze_paper(self, paper: Paper) -> Dict[str, Any]:
        """分析单篇论文"""
        logger.info(f"Analyzing paper: {paper.title}")
        
        chain = self.prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({
                "title": paper.title,
                "abstract": paper.abstract,
                "full_text": ""
            })
            
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response for paper: {paper.title}")
            return {
                "problem": "",
                "method": "",
                "dataset": "",
                "metric": "",
                "results": {},
                "limitation": "",
                "contribution": ""
            }
        except Exception as e:
            logger.error(f"Error analyzing paper {paper.title}: {str(e)}")
            return {
                "problem": "",
                "method": "",
                "dataset": "",
                "metric": "",
                "results": {},
                "limitation": "",
                "contribution": ""
            }
    
    def analyze_papers(self, papers: List[Paper]) -> List[Dict[str, Any]]:
        """批量分析论文"""
        logger.info(f"Analyzing {len(papers)} papers")
        
        analyses = []
        for paper in papers:
            analysis = self.analyze_paper(paper)
            analysis["title"] = paper.title
            analyses.append(analysis)
        
        logger.info(f"Completed analysis of {len(analyses)} papers")
        return analyses
