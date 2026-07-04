from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DocumentOut
from app.services import document_service

router = APIRouter(prefix='/documents', tags=['documents'])


@router.post('', response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form('general'),
    uploaded_by: str = Form('demo@company.com'),
    db: Session = Depends(get_db),
) -> DocumentOut:
    return document_service.upload_document(db, file, title, category, uploaded_by)


@router.get('', response_model=list[DocumentOut])
def list_documents(status: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[DocumentOut]:
    return document_service.list_documents(db, status)
