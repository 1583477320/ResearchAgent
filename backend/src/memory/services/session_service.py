"""Session lifecycle management service."""

from typing import Optional, List
from src.memory.repositories.session_repo import SessionRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SessionService:

    def __init__(self, session_repo: SessionRepo):
        self.repo = session_repo

    def create(self, session_id: str, topic: str, user_id: str = "default") -> str:
        self.repo.create(session_id, topic, user_id)
        logger.info(f"Session created: {session_id} — '{topic}'")
        return session_id

    def complete(self, session_id: str, summary: str = "", paper_count: int = 0):
        self.repo.complete(session_id, summary, paper_count)
        logger.info(f"Session completed: {session_id}")

    def fail(self, session_id: str, error: str = ""):
        self.repo.fail(session_id, error)
        logger.error(f"Session failed: {session_id} — {error}")

    def get(self, session_id: str) -> Optional[dict]:
        return self.repo.get(session_id)

    def list_recent(self, user_id: str = "default", limit: int = 20) -> List[dict]:
        return self.repo.list_by_user(user_id, limit=limit)

    def delete(self, session_id: str) -> bool:
        return self.repo.delete(session_id)

    def count(self, user_id: str = "default") -> int:
        return self.repo.count_by_user(user_id)

    # Aliases for workflow compatibility
    create_session = create
    complete_session = complete
    fail_session = fail
