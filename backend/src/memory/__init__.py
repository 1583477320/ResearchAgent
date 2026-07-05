"""Memory System — lightweight persistent memory for ResearchAgent.

Provides five memory layers:
1. Working Memory  — per-step agent execution records
2. Session Memory  — research run history and lifecycle
3. Knowledge Base  — accumulated paper analyses with FTS search
4. LLM Cache       — transparent prompt-level response caching
5. User Memory     — preferences and settings

All layers are backed by SQLite (zero external dependencies).
FAISS semantic search is available as an optional Phase 4 upgrade.

Usage:
    from src.memory import MemorySystem

    memory = MemorySystem()
    llm = memory.create_cached_llm()

    workflow = ResearchWorkflow(memory_system=memory)
    workflow.run("multi-task learning")
"""

from typing import Optional
from src.memory.database import Database
from src.memory.repositories.cache_repo import CacheRepo
from src.memory.repositories.session_repo import SessionRepo
from src.memory.repositories.working_memory_repo import WorkingMemoryRepo
from src.memory.repositories.analysis_repo import AnalysisRepo
from src.memory.services.cache_service import CacheService
from src.memory.services.session_service import SessionService
from src.memory.services.working_memory_service import WorkingMemoryService
from src.memory.services.knowledge_service import KnowledgeService
from src.memory.vector_store import VectorStore
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemorySystem:
    """Facade that ties together all memory services.

    This is the single entry point for the rest of the codebase.
    Each service is initialized eagerly with its own repository.

    Services:
        memory.cache          -> CacheService (LLM prompt caching)
        memory.session        -> SessionService (research run history)
        memory.working_memory -> WorkingMemoryService (step-by-step timeline)
        memory.knowledge      -> KnowledgeService (Phase 3)
        memory.user           -> UserService (Phase 5)
    """

    def __init__(self, db_path: Optional[str] = None, enabled: Optional[bool] = None):
        self._db_path = db_path or settings.memory_db_path
        self._enabled = enabled if enabled is not None else settings.memory_enabled

        if not self._enabled:
            logger.info("Memory system is disabled (memory_enabled=false).")
            self.db = None
            self.cache = None
            self.session = None
            self.working_memory = None
            self.knowledge = None
            self.user = None
            self.vector_store = None
            return

        self.db = Database(self._db_path)
        self.db.init_schema()

        # Phase 4: Vector store (created first, shared with cache + knowledge)
        self.vector_store = VectorStore(
            store_path=settings.vector_store_path,
            embedding_model=settings.embedding_model_name,
        )

        # Phase 1: LLM Cache (with semantic support)
        self._cache_repo = CacheRepo(self.db)
        self.cache = CacheService(
            cache_repo=self._cache_repo,
            enabled=settings.llm_cache_enabled,
            ttl_hours=settings.llm_cache_ttl_hours,
            vector_store=self.vector_store,
        )

        # Phase 2: Session + Working Memory
        self._session_repo = SessionRepo(self.db)
        self.session = SessionService(self._session_repo)

        self._wm_repo = WorkingMemoryRepo(self.db)
        self.working_memory = WorkingMemoryService(self._wm_repo)

        # Phase 3: Knowledge Base (with semantic search)
        self._analysis_repo = AnalysisRepo(self.db)
        self.knowledge = KnowledgeService(self._analysis_repo, self.vector_store)

        # Phase 5 (stub)
        self.user = None

        logger.info(
            f"Memory system ready (db={self._db_path}, "
            f"cache={'on' if self.cache.enabled else 'off'}, "
            f"session=on, working_memory=on)"
        )

    def create_cached_llm(self, **llm_kwargs):
        from src.memory.cached_llm import CachedChatOpenAI

        if not self._enabled:
            from src.utils.llm_client import get_llm_client
            return get_llm_client(**llm_kwargs)

        model_name = llm_kwargs.get("model_name") or settings.llm_model_name

        return CachedChatOpenAI(
            cache_service=self.cache,
            model_name=model_name,
            **llm_kwargs,
        )

    def close(self):
        if self.db:
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
