from typing import List, Dict, Any
import asyncio
import json
from src.schemas.paper import Paper
from src.services.paper_search import get_scholar_search_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent:
    def __init__(self):
        self.scholar_client = get_scholar_search_client()
    
    def search_papers(self, keywords: List[str], max_papers: int = 10) -> List[Paper]:
        logger.info(f"Searching papers for keywords: {keywords}")
        
        return asyncio.run(self._search_papers_async(keywords, max_papers))
    
    async def _search_papers_async(self, keywords: List[str], max_papers: int) -> List[Paper]:
        all_papers = []
        seen_titles = set()
        
        for keyword in keywords:
            try:
                results = await self.scholar_client.search(keyword, max_papers)
                papers_data = results.get("papers", []) if isinstance(results, dict) else results
                
                for result in papers_data:
                    if result["title"] not in seen_titles:
                        seen_titles.add(result["title"])
                        authors_data = result.get("authors", [])
                        if isinstance(authors_data, list):
                            authors = [author.get("name", "") for author in authors_data]
                        elif isinstance(authors_data, str):
                            authors = [a.strip() for a in authors_data.split(",")]
                        else:
                            authors = []
                        
                        year = result.get("year", "")
                        if isinstance(year, int):
                            year = str(year)
                        if not year and result.get("publicationDate"):
                            pub_date = result["publicationDate"]
                            year = str(pub_date)[:4] if pub_date else ""
                        
                        abstract = result.get("abstract", "")
                        if abstract is None:
                            abstract = ""
                        
                        paper = Paper(
                            title=result["title"],
                            authors=authors,
                            abstract=abstract,
                            publication_date=year,
                            url=result.get("url", ""),
                            pdf_url=result.get("pdfUrl") or result.get("pdf_url"),
                            source=result.get("source", "Google Scholar (MCP)").capitalize()
                        )
                        all_papers.append(paper)
            except Exception as e:
                logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
        
        return all_papers[:max_papers]
    
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
