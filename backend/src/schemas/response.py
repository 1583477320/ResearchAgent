from typing import List, Optional
from pydantic import BaseModel
from .paper import Paper


class TaskStatus(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    progress: float = 0.0


class ResearchReport(BaseModel):
    topic: str
    summary: str
    papers: List[Paper]
    research_trends: str
    key_findings: List[str]
    references: List[str]


class ReportResponse(BaseModel):
    success: bool
    report: Optional[ResearchReport] = None
    error: Optional[str] = None
