from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ApprovalDecisionIn
from app.services.approval_service import decide_approval, list_approvals

router = APIRouter(prefix='/approvals', tags=['approvals'])


@router.get('')
def approvals(status: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return list_approvals(db, status)


@router.post('/{approval_id}/approve')
def approve(approval_id: str, payload: ApprovalDecisionIn, db: Session = Depends(get_db)) -> dict:
    return decide_approval(db, approval_id, 'approved', payload)


@router.post('/{approval_id}/reject')
def reject(approval_id: str, payload: ApprovalDecisionIn, db: Session = Depends(get_db)) -> dict:
    return decide_approval(db, approval_id, 'rejected', payload)
