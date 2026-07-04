from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    title: str
    category: str
    version: int
    status: str
    file_name: str
    uploaded_by: str
    created_at: datetime
    chunk_count: int


class CitationOut(BaseModel):
    document_id: str
    document_title: str
    version: int
    chunk_id: str
    sentence: str
    score: float


class QuestionIn(BaseModel):
    question: str = Field(min_length=2)
    requester_email: str = 'demo@company.com'
    top_k: int = Field(default=4, ge=1, le=10)


class AnswerOut(BaseModel):
    request_id: str
    answer: str
    confidence: float
    needs_review: bool
    citations: list[CitationOut]


class DraftIn(BaseModel):
    draft_type: Literal['email', 'report', 'meeting_summary', 'work_request']
    instruction: str = Field(min_length=5)
    requester_email: str = 'demo@company.com'
    related_question: str | None = None


class DraftOut(BaseModel):
    request_id: str
    approval_id: str
    draft_type: str
    draft: str
    status: str


class ApprovalDecisionIn(BaseModel):
    approver_email: str
    comment: str | None = None
    final_payload: str | None = None


class HistoryOut(BaseModel):
    id: str
    request_type: str
    prompt: str
    response: str
    confidence: float
    status: str
    requester_email: str
    created_at: datetime
