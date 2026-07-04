import uuid

from sqlalchemy.orm import Session

from app.models import RequestRecord
from app.schemas import AnswerOut, QuestionIn
from app.services.audit_service import log_event
from app.services.retrieval_service import build_answer, search_chunks


def answer_question(db: Session, payload: QuestionIn) -> AnswerOut:
    results = search_chunks(db, payload.question, payload.top_k)
    answer, confidence, citations = build_answer(payload.question, results)
    request = RequestRecord(
        id=str(uuid.uuid4()),
        request_type='rag_answer',
        prompt=payload.question,
        response=answer,
        confidence=confidence,
        status='needs_review' if confidence < 0.45 else 'completed',
        requester_email=payload.requester_email,
        citations=[citation.model_dump() for citation in citations],
    )
    db.add(request)
    log_event(db, payload.requester_email, 'rag.asked', 'request', request.id, {'confidence': confidence})
    db.commit()
    return AnswerOut(request_id=request.id, answer=answer, confidence=confidence, needs_review=confidence < 0.45, citations=citations)
