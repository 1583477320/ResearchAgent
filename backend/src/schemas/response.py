from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .paper import Paper


class TaskStatus(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    progress: float = 0.0


class ReportResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
