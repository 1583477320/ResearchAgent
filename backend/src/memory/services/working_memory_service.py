"""Working memory service — records agent execution steps."""

from typing import List
from src.memory.repositories.working_memory_repo import WorkingMemoryRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WorkingMemoryService:

    def __init__(self, repo: WorkingMemoryRepo):
        self.repo = repo

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
    ):
        entry_id = self.repo.record(
            session_id=session_id,
            node_name=node_name,
            agent_name=agent_name,
            step_number=step_number,
            input_preview=input_preview[:500],
            output_preview=output_preview[:500],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        logger.debug(f"Memory recorded: {node_name}/{agent_name} (step {step_number})")
        return entry_id

    def timeline(self, session_id: str) -> List[dict]:
        return self.repo.timeline(session_id)

    def summary(self, session_id: str, last_n: int = 10) -> str:
        """Build a readable context summary of the last N steps."""
        steps = self.repo.timeline(session_id)
        recent = steps[-last_n:] if len(steps) > last_n else steps
        lines = []
        for s in recent:
            lines.append(
                f"[{s['node_name']}] {s['agent_name']}: "
                f"in={s['input_preview'][:100]} → out={s['output_preview'][:100]}"
            )
        return "\n".join(lines)
