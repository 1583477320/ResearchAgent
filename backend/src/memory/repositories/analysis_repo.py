"""Repository for paper analysis records with FTS5 full-text search."""

from typing import List, Optional
from .base_repo import BaseRepo


class AnalysisRepo(BaseRepo):
    """CRUD + FTS5 search for paper_analyses table."""

    def save(self, session_id: str, paper_title: str, paper_url: str = "",
             problem: str = "", method: str = "", dataset: str = "",
             metric: str = "", results: str = "{}",
             limitation: str = "", contribution: str = "") -> str:
        from src.memory.models import PaperAnalysisRecord

        record = PaperAnalysisRecord(
            session_id=session_id,
            paper_title=paper_title,
            paper_url=paper_url,
            problem=problem,
            method=method,
            dataset=dataset,
            metric=metric,
            results=results,
            limitation=limitation,
            contribution=contribution,
        )
        self.insert("paper_analyses", record.model_dump())
        return record.id

    def get_by_title(self, title: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM paper_analyses WHERE paper_title = ? ORDER BY created_at DESC LIMIT 1",
            (title,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_session(self, session_id: str) -> List[dict]:
        rows = self.list_all(
            "paper_analyses",
            where="session_id = ?",
            params=(session_id,),
            order_by="created_at ASC",
            limit=200,
        )
        return [dict(r) for r in rows]

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """FTS5 full-text search across paper analyses.

        Searches title, problem, method, dataset, limitation, and contribution fields.
        The query is passed directly to FTS5 which supports boolean operators:
          "multi-task AND learning"  → both terms required
          "transformer OR attention" → either term
          "meta -learning"           → first term, exclude second
        """
        # Wrap each term so partial matches work; simple FTS5 syntax
        fts_query = " OR ".join(query.split())
        rows = self.conn.execute(
            """SELECT pa.*, rank
               FROM paper_analyses_fts fts
               JOIN paper_analyses pa ON pa.rowid = fts.rowid
               WHERE paper_analyses_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (fts_query, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_papers(self, limit: int = 50, offset: int = 0) -> List[dict]:
        rows = self.list_all("paper_analyses", limit=limit, offset=offset)
        return [dict(r) for r in rows]

    def count_all(self) -> int:
        return self.count("paper_analyses")
