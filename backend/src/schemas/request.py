from pydantic import BaseModel


class ResearchRequest(BaseModel):
    topic: str
    max_papers: int = 10
