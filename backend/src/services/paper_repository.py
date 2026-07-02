from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
import urllib.request
import urllib.error
from io import BytesIO
import fitz  # PyMuPDF
from src.schemas.paper import Paper
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PaperRepository:
    def __init__(self, repo_path: str = "research_repo"):
        self.repo_path = Path(repo_path)
        self.papers_dir = self.repo_path / "papers"
        self.docs_dir = self.repo_path / "docs"
        self.metadata_file = self.repo_path / "metadata.json"
        
        self._init_repo()
    
    def _init_repo(self):
        """初始化仓库目录结构"""
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.metadata_file.exists():
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({"papers": [], "next_id": 1}, f)
    
    def _generate_paper_id(self, title: str) -> str:
        """根据标题生成唯一ID"""
        return hashlib.md5(title.encode("utf-8")).hexdigest()[:16]
    
    def _download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """下载PDF文件"""
        try:
            with urllib.request.urlopen(pdf_url, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            logger.error(f"Failed to download PDF: {e}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL error: {e}")
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _parse_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """解析PDF内容"""
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            text = ""
            for page in doc:
                text += page.get_text()
            
            metadata = doc.metadata
            
            return {
                "text": text,
                "page_count": len(doc),
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return {"text": "", "page_count": 0, "metadata": {}}
    
    def _generate_md(self, paper: Paper, pdf_info: Dict[str, Any]) -> str:
        """生成Markdown文档"""
        paper_id = self._generate_paper_id(paper.title)
        
        md = f"# {paper.title}\n\n"
        
        md += "## 一、基本信息\n\n"
        md += "| 字段 | 内容 |\n"
        md += "|------|------|\n"
        md += f"| 作者 | {', '.join(paper.authors)} |\n"
        md += f"| 年份 | {paper.publication_date} |\n"
        md += f"| 来源 | {paper.source} |\n"
        md += f"| 链接 | [{paper.url}]({paper.url}) |\n"
        if paper.pdf_url:
            md += f"| PDF | [下载]({paper_id}.pdf) |\n"
        md += "\n"
        
        md += "## 二、摘要\n\n"
        md += paper.abstract if paper.abstract else "暂无摘要\n\n"
        
        if pdf_info.get("text"):
            md += "## 三、论文正文\n\n"
            md += pdf_info["text"][:5000]  # 截取前5000字符
            if len(pdf_info["text"]) > 5000:
                md += "\n\n...（全文已截断）\n\n"
        
        md += "## 四、元数据\n\n"
        md += f"- 页数: {pdf_info.get('page_count', 0)}\n"
        if pdf_info.get("metadata"):
            for key, value in pdf_info["metadata"].items():
                if value:
                    md += f"- {key}: {value}\n"
        
        return md
    
    def add_paper(self, paper: Paper) -> bool:
        """添加论文到仓库"""
        paper_id = self._generate_paper_id(paper.title)
        
        # 检查是否已存在
        existing_ids = self._get_existing_ids()
        if paper_id in existing_ids:
            logger.info(f"Paper already exists: {paper.title}")
            return False
        
        pdf_info = {"text": "", "page_count": 0, "metadata": {}}
        
        # 下载并解析PDF
        if paper.pdf_url:
            logger.info(f"Downloading PDF for: {paper.title}")
            pdf_content = self._download_pdf(paper.pdf_url)
            if pdf_content:
                pdf_path = self.papers_dir / f"{paper_id}.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)
                
                pdf_info = self._parse_pdf(pdf_content)
        
        # 生成MD文件
        md_content = self._generate_md(paper, pdf_info)
        md_path = self.docs_dir / f"{paper_id}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        # 更新元数据
        self._update_metadata(paper, paper_id)
        
        logger.info(f"Added paper to repository: {paper.title}")
        return True
    
    def add_papers(self, papers: List[Paper]) -> int:
        """批量添加论文"""
        count = 0
        for paper in papers:
            if self.add_paper(paper):
                count += 1
        return count
    
    def _get_existing_ids(self) -> set:
        """获取已存在的论文ID"""
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {p["id"] for p in data["papers"]}
    
    def _update_metadata(self, paper: Paper, paper_id: str):
        """更新元数据索引"""
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        entry = {
            "id": paper_id,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.publication_date,
            "source": paper.source,
            "url": paper.url,
            "pdf_url": paper.pdf_url,
            "has_pdf": bool(paper.pdf_url),
            "added_at": str(paper.publication_date)
        }
        
        data["papers"].append(entry)
        
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索仓库中的论文"""
        results = []
        
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for paper in data["papers"]:
            if (query.lower() in paper["title"].lower() or
                query.lower() in " ".join(paper["authors"]).lower()):
                results.append(paper)
        
        return results
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取论文信息"""
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for paper in data["papers"]:
            if paper["id"] == paper_id:
                return paper
        return None
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """获取所有论文"""
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["papers"]
    
    def get_paper_count(self) -> int:
        """获取论文数量"""
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data["papers"])


def get_paper_repository(repo_path: str = "research_repo") -> PaperRepository:
    """获取论文仓库实例"""
    return PaperRepository(repo_path)
