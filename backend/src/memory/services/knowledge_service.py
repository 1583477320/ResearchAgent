"""Knowledge base service — accumulate and search paper analyses."""

import json
from typing import List, Optional
from src.memory.repositories.analysis_repo import AnalysisRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeService:

    def __init__(self, repo: AnalysisRepo, vector_store=None):
        self.repo = repo
        self.vector_store = vector_store

    def save_analysis(self, session_id: str, paper_title: str, analysis: dict):
        """Persist a paper analysis into the knowledge base."""
        results_json = json.dumps(analysis.get("results", {}), ensure_ascii=False)
        self.repo.save(
            session_id=session_id,
            paper_title=paper_title,
            paper_url=analysis.get("url", ""),
            problem=analysis.get("problem", ""),
            method=analysis.get("method", ""),
            dataset=analysis.get("dataset", ""),
            metric=analysis.get("metric", ""),
            results=results_json,
            limitation=analysis.get("limitation", ""),
            contribution=analysis.get("contribution", ""),
        )

        # Also index into FAISS for semantic search
        if self.vector_store and self.vector_store.enabled:
            text = f"{paper_title}. {analysis.get('problem', '')}. {analysis.get('method', '')}. {analysis.get('contribution', '')}"
            self.vector_store.add(
                [text],
                [{"title": paper_title, "session_id": session_id}],
            )
            self.vector_store.save()

        logger.debug(f"Knowledge saved: '{paper_title[:60]}'")

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """FTS5 full-text search. Returns matching paper analyses ranked by relevance."""
        return self.repo.search(query, limit)

    def search_semantic(self, query: str, limit: int = 5) -> List[dict]:
        """FAISS semantic search. Returns semantically similar papers.

        Falls back to FTS if vector store is not enabled.
        """
        if not self.vector_store or not self.vector_store.enabled:
            return self.search(query, limit)

        results = self.vector_store.search(query, k=limit)
        output = []
        for r in results:
            title = r["metadata"].get("title", "")
            if title:
                paper = self.repo.get_by_title(title)
                if paper:
                    paper["semantic_score"] = r["score"]
                    output.append(paper)
        return output

    def get_by_title(self, title: str) -> Optional[dict]:
        return self.repo.get_by_title(title)

    def list_by_session(self, session_id: str) -> List[dict]:
        return self.repo.list_by_session(session_id)

    def list_all(self, limit: int = 50, offset: int = 0) -> List[dict]:
        return self.repo.list_all_papers(limit, offset)

    def total(self) -> int:
        return self.repo.count_all()

    def index_all(self):
        """(Re)index all existing paper analyses into FAISS."""
        if not self.vector_store or not self.vector_store.enabled:
            return 0

        papers = self.repo.list_all_papers(limit=10000)
        texts = []
        metadata = []
        for p in papers:
            text = f"{p.get('paper_title', '')}. {p.get('problem', '')}. {p.get('method', '')}. {p.get('contribution', '')}"
            texts.append(text)
            metadata.append({"title": p.get("paper_title", ""), "session_id": p.get("session_id", "")})

        if texts:
            self.vector_store.add(texts, metadata)
            self.vector_store.save()
            logger.info(f"Indexed {len(texts)} papers into FAISS")

        return len(texts)
