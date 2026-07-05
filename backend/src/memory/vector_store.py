"""FAISS vector store for semantic paper and prompt search."""

import json
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import faiss

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS-based semantic search over paper analyses and prompts.

    Uses the configured LLM provider's embedding API (OpenAI-compatible).
    Set embedding_model_name in .env to enable (e.g. "text-embedding-3-small").
    Leave empty to disable semantic search entirely.

    Usage:
        store = VectorStore(embedding_model="text-embedding-3-small")
        store.add(["paper abstract 1", "paper abstract 2"], [{"id": 1}, {"id": 2}])
        results = store.search("transformer attention mechanism", k=5)
        # -> [{"score": 0.95, "metadata": {"id": 1}}, ...]
        store.save()
    """

    def __init__(self, store_path: str = "", embedding_model: str = ""):
        self.store_path = store_path or settings.vector_store_path
        self.embedding_model = embedding_model or settings.embedding_model_name
        self._enabled = bool(self.embedding_model)

        self._index: Optional[faiss.IndexFlatIP] = None
        self._metadata: List[dict] = []
        self._dimension: int = 0
        self._embedder = None

        if self._enabled:
            self._init_embedder()
            self.load()

    def _init_embedder(self):
        from langchain_openai import OpenAIEmbeddings

        provider = settings.llm_provider.lower()
        if provider == "deepseek":
            api_key = settings.deepseek_api_key
            base_url = settings.deepseek_api_base_url
        elif provider == "qwen":
            api_key = settings.llm_api_key
            base_url = settings.llm_api_base_url
        else:
            api_key = settings.openai_api_key
            base_url = settings.openai_api_base_url

        self._embedder = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=api_key,
            openai_api_base=base_url,
        )
        # Probe dimension with a short text
        probe = self._embedder.embed_query("probe")
        self._dimension = len(probe)
        logger.info(
            f"Embedding model ready: {self.embedding_model} "
            f"(dim={self._dimension})"
        )

    @property
    def enabled(self) -> bool:
        return self._enabled and self._embedder is not None

    # ── index operations ──────────────────────────────────────

    def _ensure_index(self):
        if self._index is None:
            self._index = faiss.IndexFlatIP(self._dimension)

    def add(self, texts: List[str], metadata: List[dict] = None) -> int:
        """Embed texts and add to the index. Returns number of vectors added."""
        if not self.enabled or not texts:
            return 0

        vectors = self._embedder.embed_documents(texts)
        matrix = np.array(vectors, dtype=np.float32)

        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(matrix)

        self._ensure_index()
        self._index.add(matrix)

        if metadata is None:
            metadata = [{}] * len(texts)
        self._metadata.extend(metadata)

        logger.debug(f"Added {len(texts)} vectors to FAISS index (total={self._index.ntotal})")
        return len(texts)

    def search(self, query: str, k: int = 5) -> List[dict]:
        """Search for texts similar to query. Returns [{score, metadata}, ...]."""
        if not self.enabled or self._index is None or self._index.ntotal == 0:
            return []

        vec = self._embedder.embed_query(query)
        vec = np.array([vec], dtype=np.float32)
        faiss.normalize_L2(vec)

        scores, indices = self._index.search(vec, min(k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            results.append({
                "score": float(score),
                "metadata": self._metadata[idx],
            })
        return results

    # ── persistence ───────────────────────────────────────────

    def save(self):
        """Save index and metadata to disk."""
        if not self.enabled or self._index is None:
            return

        path = Path(self.store_path)
        path.mkdir(parents=True, exist_ok=True)

        index_path = path / "paper_index.faiss"
        meta_path = path / "metadata.json"

        faiss.write_index(self._index, str(index_path))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)

        logger.info(
            f"FAISS index saved: {self._index.ntotal} vectors → {index_path}"
        )

    def load(self):
        """Load index and metadata from disk. No-op if files don't exist."""
        index_path = Path(self.store_path) / "paper_index.faiss"
        meta_path = Path(self.store_path) / "metadata.json"

        if not index_path.exists():
            logger.debug("No existing FAISS index found — starting fresh.")
            return

        try:
            self._index = faiss.read_index(str(index_path))
            self._dimension = self._index.d

            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)

            logger.info(
                f"FAISS index loaded: {self._index.ntotal} vectors "
                f"(dim={self._dimension}) from {index_path}"
            )
        except Exception as e:
            logger.warning(f"Failed to load FAISS index: {e} — starting fresh.")
            self._index = None
            self._metadata = []

    # ── index stats ───────────────────────────────────────────

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index else 0
