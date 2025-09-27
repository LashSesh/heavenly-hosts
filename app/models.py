from pydantic import BaseModel
from typing import List


class InjectRequest(BaseModel):
    signal_vector: List[float]
    timestamp: float
    semantic_tag: str


class QueryRequest(BaseModel):
    signal_vector: List[float]
    threshold: float


class MessageFragment(BaseModel):
    content: str
    fragment_size: int = 16
