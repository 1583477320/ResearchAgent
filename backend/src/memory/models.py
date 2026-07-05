"""Pydantic data models for the memory system."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from uuid import uuid4


def _new_id() -> str:
    return uuid4().hex[:16]


class SessionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchSession(BaseModel):
    """A single research run from topic submission to final report."""

    id: str = Field(default_factory=_new_id)
    user_id: str = "default"
    topic: str
    status: str = SessionStatus.RUNNING.value
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    paper_count: int = 0
    summary: str = ""
    error_message: str = ""
    api_task_id: str = ""


class MemoryEntry(BaseModel):
    """Single step in a research session's working memory."""

    id: str = Field(default_factory=_new_id)
    session_id: str
    node_name: str  # plan, research, read, gap_analysis, ...
    agent_name: str  # planner, researcher, reader, gap, ...
    step_number: int
    input_preview: str = ""
    output_preview: str = ""
    input_token_count: int = 0
    output_token_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaperAnalysisRecord(BaseModel):
    """Structured analysis of a single paper, from the ReadingAgent."""

    id: str = Field(default_factory=_new_id)
    session_id: str
    paper_title: str
    paper_url: str = ""
    problem: str = ""
    method: str = ""
    dataset: str = ""
    metric: str = ""
    results: str = "{}"  # JSON string
    limitation: str = ""
    contribution: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LLMCacheEntry(BaseModel):
    """Cache of an LLM invocation result."""

    id: str = Field(default_factory=_new_id)
    model_name: str
    prompt_hash: str  # SHA-256 of (system_prompt + user_prompt)
    system_prompt: str = ""
    user_prompt: str = ""
    response_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hit_count: int = 1
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class UserPreference(BaseModel):
    """Key-value user preferences."""

    key: str
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
