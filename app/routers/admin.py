from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DocumentOut
from app.services import document_service

router = APIRouter(prefix='/admin', tags=['admin'])


@router.patch('/documents/{document_id}/status', response_model=DocumentOut)
def update_document_status(
    document_id: str,
    status: Literal['active', 'archived', 'disabled'],
    actor: str = Query('admin@company.com'),
    db: Session = Depends(get_db),
) -> DocumentOut:
    return document_service.update_document_status(db, document_id, status, actor)
