"""Repository for working memory entries."""

from typing import List
from datetime import datetime
from .base_repo import BaseRepo


class WorkingMemoryRepo(BaseRepo):
    """CRUD for working_memory_entries table."""

    def record(
        self,
        session_id: str,
        node_name: str,
        agent_name: str,
        step_number: int,
        input_preview: str = "",
        output_preview: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> str:
        from src.memory.models import MemoryEntry

        entry = MemoryEntry(
            session_id=session_id,
            node_name=node_name,
            agent_name=agent_name,
            step_number=step_number,
            input_preview=input_preview[:500],
            output_preview=output_preview[:500],
            input_token_count=input_tokens,
            output_token_count=output_tokens,
        )
        data = entry.model_dump()
        data["created_at"] = entry.created_at.isoformat()
        self.insert("working_memory_entries", data)
        return entry.id

    def timeline(self, session_id: str) -> List[dict]:
        rows = self.list_all(
            "working_memory_entries",
            where="session_id = ?",
            params=(session_id,),
            order_by="step_number ASC",
            limit=100,
        )
        return [dict(r) for r in rows]

    def delete_by_session(self, session_id: str) -> int:
        c = self.conn.execute(
            "DELETE FROM working_memory_entries WHERE session_id = ?",
            (session_id,),
        )
        self.conn.commit()
        return c.rowcount
