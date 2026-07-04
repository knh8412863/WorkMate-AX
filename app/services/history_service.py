from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RequestRecord
from app.schemas import HistoryOut


def list_request_history(db: Session, requester_email: str | None = None) -> list[HistoryOut]:
    statement = select(RequestRecord).order_by(RequestRecord.created_at.desc())
    if requester_email:
        statement = statement.where(RequestRecord.requester_email == requester_email)
    return [HistoryOut.model_validate(record, from_attributes=True) for record in db.scalars(statement).all()]
