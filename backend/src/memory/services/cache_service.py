"""LLM cache service — prompt hashing and cache lookup logic."""

import hashlib
import re
from typing import Optional
from src.memory.repositories.cache_repo import CacheRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

_NORMALIZE_PATTERNS = [
    (re.compile(r'\d{4}-\d{2}-\d{2}'), "YYYY-MM-DD"),
    (re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'), "IP_ADDR"),
]


class CacheService:
    """LLM response cache with exact-match (hash) and semantic (FAISS) lookup."""

    def __init__(self, cache_repo: CacheRepo, enabled: bool = True,
                 ttl_hours: int = 48, vector_store=None,
                 semantic_threshold: float = 0.92):
        self.repo = cache_repo
        self.enabled = enabled
        self.ttl_hours = ttl_hours
        self.vector_store = vector_store
        self.semantic_threshold = semantic_threshold
        # Track prompt vectors for semantic cache (separate from paper vectors)
        self._prompt_ids: set = set()  # ids of cache entries indexed in vector store

    def hash_prompt(self, system_prompt: str, user_prompt: str) -> str:
        combined = self._normalize(system_prompt) + "|||" + self._normalize(user_prompt)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.strip()
        for pattern, replacement in _NORMALIZE_PATTERNS:
            normalized = pattern.sub(replacement, normalized)
        return normalized

    # ── exact-match cache ──────────────────────────────────────

    def get(self, model_name: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.enabled:
            return None
        prompt_hash = self.hash_prompt(system_prompt, user_prompt)
        response = self.repo.get_response(model_name, prompt_hash)
        if response:
            logger.info(f"LLM cache HIT (exact) model={model_name}")
        return response

    def get_semantic(self, model_name: str, system_prompt: str,
                     user_prompt: str) -> Optional[str]:
        """Check if a semantically similar prompt has been cached.

        Uses FAISS to find the nearest cached prompt. If the cosine
        similarity exceeds semantic_threshold, return the cached response.
        """
        if not self.enabled or not self.vector_store or not self.vector_store.enabled:
            return None
        if self.vector_store.size == 0:
            return None

        query_text = system_prompt + " " + user_prompt
        results = self.vector_store.search(query_text, k=1)
        if not results:
            return None

        best = results[0]
        if best["score"] < self.semantic_threshold:
            return None

        meta = best["metadata"]
        if meta.get("type") != "prompt_cache":
            return None

        prompt_hash = meta.get("prompt_hash", "")
        response = self.repo.get_response(model_name, prompt_hash)
        if response:
            logger.info(
                f"LLM cache HIT (semantic, score={best['score']:.3f}) "
                f"model={model_name}"
            )
        return response

    def set(self, model_name: str, system_prompt: str,
            user_prompt: str, response_text: str) -> None:
        if not self.enabled:
            return
        prompt_hash = self.hash_prompt(system_prompt, user_prompt)
        entry_id = self.repo.save(
            model_name=model_name,
            prompt_hash=prompt_hash,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_text=response_text,
        )

        # Index prompt for semantic lookup
        if self.vector_store and self.vector_store.enabled:
            query_text = system_prompt + " " + user_prompt
            self.vector_store.add(
                [query_text],
                [{"type": "prompt_cache", "prompt_hash": prompt_hash, "id": entry_id}],
            )
            self._prompt_ids.add(entry_id)
            self.vector_store.save()

        logger.debug(f"LLM cache STORED model={model_name}")

    def delete_by_model(self, model_name: str) -> int:
        db = self.repo.db
        cursor = db.conn.execute(
            "DELETE FROM llm_cache WHERE model_name = ?", (model_name,)
        )
        db.conn.commit()
        logger.info(f"Cleared {cursor.rowcount} cache entries for model={model_name}")
        return cursor.rowcount

    def prune_old(self) -> int:
        count = self.repo.prune_old(self.ttl_hours)
        if count > 0:
            logger.info(f"Pruned {count} expired cache entries (TTL={self.ttl_hours}h)")
        return count

    def stats(self) -> dict:
        base = self.repo.stats()
        base["semantic_enabled"] = bool(
            self.vector_store and self.vector_store.enabled
        )
        return base
