from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def log_event(db: Session, actor: str, action: str, target_type: str, target_id: str, metadata: dict | None = None) -> None:
    db.add(AuditLog(actor=actor, action=action, target_type=target_type, target_id=target_id, metadata_json=metadata or {}))


def list_audit_logs(db: Session, limit: int = 50) -> list[dict]:
    limit = max(1, min(200, limit))
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [
        {
            'id': log.id,
            'created_at': log.created_at,
            'actor': log.actor,
            'action': log.action,
            'target_type': log.target_type,
            'target_id': log.target_id,
            'metadata': log.metadata_json,
        }
        for log in logs
    ]
