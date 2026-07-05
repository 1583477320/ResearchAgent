"""Repository for LLM cache entries."""

import sqlite3
from typing import Optional, List
from datetime import datetime
from .base_repo import BaseRepo


class CacheRepo(BaseRepo):
    """CRUD operations for the llm_cache table."""

    def save(
        self,
        model_name: str,
        prompt_hash: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
    ) -> str:
        """Insert or update a cache entry. Returns the entry id."""
        now = datetime.utcnow().isoformat()
        existing = self.get_by_hash(model_name, prompt_hash)
        if existing:
            # Update hit count and last_accessed
            self.update(
                "llm_cache",
                existing["id"],
                {
                    "hit_count": existing["hit_count"] + 1,
                    "last_accessed": now,
                },
            )
            return existing["id"]
        else:
            from src.memory.models import LLMCacheEntry

            entry = LLMCacheEntry(
                model_name=model_name,
                prompt_hash=prompt_hash,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_text=response_text,
            )
            self.insert("llm_cache", entry.model_dump())
            return entry.id

    def get_by_hash(self, model_name: str, prompt_hash: str) -> Optional[sqlite3.Row]:
        """Find a cache entry by model + hash. Also updates last_accessed."""
        row = self.conn.execute(
            "SELECT * FROM llm_cache WHERE model_name = ? AND prompt_hash = ?",
            (model_name, prompt_hash),
        ).fetchone()
        if row:
            # Update access time in background
            self.conn.execute(
                "UPDATE llm_cache SET last_accessed = ?, hit_count = hit_count + 1 WHERE id = ?",
                (datetime.utcnow().isoformat(), row["id"]),
            )
            self.conn.commit()
        return row

    def get_response(self, model_name: str, prompt_hash: str) -> Optional[str]:
        """Get the cached response text for a given model+hash, or None."""
        row = self.get_by_hash(model_name, prompt_hash)
        return row["response_text"] if row else None

    def prune_old(self, ttl_hours: int = 48) -> int:
        """Delete entries older than ttl_hours. Returns count deleted."""
        cursor = self.conn.execute(
            f"DELETE FROM llm_cache WHERE created_at < datetime('now', '-{ttl_hours} hours')"
        )
        self.conn.commit()
        return cursor.rowcount

    def list_recent(self, limit: int = 20) -> List[sqlite3.Row]:
        """List most recently accessed cache entries."""
        return self.list_all("llm_cache", order_by="last_accessed DESC", limit=limit)

    def stats(self) -> dict:
        """Return cache statistics."""
        total = self.count("llm_cache")
        total_hits = self.conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM llm_cache"
        ).fetchone()[0]
        return {
            "total_entries": total,
            "total_hits": total_hits,
        }
