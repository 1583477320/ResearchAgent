from typing import Optional, List
from pydantic import BaseModel


class ResearchRequest(BaseModel):
    topic: str
    max_papers: int = 10
    venues: Optional[List[str]] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
