from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Approval, RequestRecord
from app.schemas import ApprovalDecisionIn
from app.services.audit_service import log_event


def list_approvals(db: Session, status: str | None = None) -> list[dict]:
    statement = select(Approval).order_by(Approval.created_at.desc())
    if status:
        statement = statement.where(Approval.status == status)
    approvals = db.scalars(statement).all()
    requests = {request.id: request for request in db.scalars(select(RequestRecord)).all()}
    return [
        {
            'approval_id': approval.id,
            'request_id': approval.request_id,
            'status': approval.status,
            'approver_email': approval.approver_email,
            'comment': approval.comment,
            'request_type': requests[approval.request_id].request_type if approval.request_id in requests else None,
            'prompt': requests[approval.request_id].prompt if approval.request_id in requests else None,
            'draft': requests[approval.request_id].response if approval.request_id in requests else None,
            'created_at': approval.created_at,
            'updated_at': approval.updated_at,
        }
        for approval in approvals
    ]


def decide_approval(db: Session, approval_id: str, decision: str, payload: ApprovalDecisionIn) -> dict:
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail='approval not found')
    if approval.status != 'pending':
        raise HTTPException(status_code=409, detail='approval already decided')
    request = db.get(RequestRecord, approval.request_id)
    if not request:
        raise HTTPException(status_code=404, detail='request not found')

    approval.status = decision
    approval.approver_email = payload.approver_email
    approval.comment = payload.comment
    approval.final_payload = payload.final_payload or request.response
    request.status = 'approved' if decision == 'approved' else 'rejected'
    if payload.final_payload:
        request.response = payload.final_payload
    log_event(db, payload.approver_email, f'approval.{decision}', 'approval', approval.id, {'request_id': request.id})
    db.commit()
    return {'approval_id': approval.id, 'request_id': request.id, 'status': approval.status, 'final_payload': approval.final_payload}
