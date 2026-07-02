from typing import List, Optional
from pydantic import BaseModel


class Paper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    publication_date: str
    source: str = "arXiv"
    url: str
    pdf_url: Optional[str] = None
    keywords: List[str] = []
