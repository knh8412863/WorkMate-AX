from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HistoryOut
from app.services.audit_service import list_audit_logs
from app.services.history_service import list_request_history

router = APIRouter(tags=['history'])


@router.get('/history', response_model=list[HistoryOut])
def request_history(requester_email: str | None = None, db: Session = Depends(get_db)) -> list[HistoryOut]:
    return list_request_history(db, requester_email)


@router.get('/audit-logs')
def audit_logs(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> list[dict]:
    return list_audit_logs(db, limit)
