"""Repository for research session records."""

from typing import Optional, List
from datetime import datetime
from .base_repo import BaseRepo


class SessionRepo(BaseRepo):
    """CRUD for research_sessions table."""

    def create(self, session_id: str, topic: str, user_id: str = "default") -> str:
        self.insert("research_sessions", {
            "id": session_id,
            "user_id": user_id,
            "topic": topic,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        })
        return session_id

    def complete(self, session_id: str, summary: str = "", paper_count: int = 0) -> bool:
        return self.update("research_sessions", session_id, {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "paper_count": paper_count,
        })

    def fail(self, session_id: str, error: str = "") -> bool:
        return self.update("research_sessions", session_id, {
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": error,
        })

    def get(self, session_id: str) -> Optional[dict]:
        row = self.get_by_id("research_sessions", session_id)
        return dict(row) if row else None

    def list_by_user(self, user_id: str = "default", limit: int = 20, offset: int = 0) -> List[dict]:
        rows = self.list_all(
            "research_sessions",
            where="user_id = ?",
            params=(user_id,),
            order_by="started_at DESC",
            limit=limit,
            offset=offset,
        )
        return [dict(r) for r in rows]

    def delete(self, session_id: str) -> bool:
        return super().delete("research_sessions", session_id)

    def count_by_user(self, user_id: str = "default") -> int:
        return self.count("research_sessions", "user_id = ?", (user_id,))
