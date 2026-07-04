import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.models import Document, DocumentChunk
from app.schemas import DocumentOut
from app.services.audit_service import log_event
from app.utils.text import chunk_text, to_term_vector, tokenize

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == '.pdf':
        if PdfReader is None:
            raise HTTPException(status_code=400, detail='PDF support requires pypdf. Run: pip install -e .')
        reader = PdfReader(str(file_path))
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    return file_path.read_text(encoding='utf-8', errors='ignore')


def serialize_document(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        title=document.title,
        category=document.category,
        version=document.version,
        status=document.status,
        file_name=document.file_name,
        uploaded_by=document.uploaded_by,
        created_at=document.created_at,
        chunk_count=len(document.chunks),
    )


def upload_document(db: Session, file: UploadFile, title: str, category: str, uploaded_by: str) -> DocumentOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail='file name is required')
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {'.pdf', '.txt', '.md'}:
        raise HTTPException(status_code=400, detail='supported file types: pdf, txt, md')

    latest_version = db.scalar(select(Document.version).where(Document.title == title).order_by(Document.version.desc())) or 0
    document_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f'{document_id}{suffix}'
    with file_path.open('wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text(file_path)
    chunks = chunk_text(text)
    if not chunks:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail='no extractable text found')

    document = Document(
        id=document_id,
        title=title,
        category=category,
        version=latest_version + 1,
        file_name=file.filename,
        file_path=str(file_path),
        uploaded_by=uploaded_by,
    )
    document.chunks = [
        DocumentChunk(chunk_index=index, content=chunk, token_count=len(tokenize(chunk)), term_vector=to_term_vector(chunk))
        for index, chunk in enumerate(chunks)
    ]
    db.add(document)
    log_event(db, uploaded_by, 'document.uploaded', 'document', document.id, {'title': title, 'version': document.version})
    db.commit()
    db.refresh(document)
    return serialize_document(document)


def list_documents(db: Session, status: str | None = None) -> list[DocumentOut]:
    statement = select(Document).order_by(Document.created_at.desc())
    if status:
        statement = statement.where(Document.status == status)
    return [serialize_document(document) for document in db.scalars(statement).all()]


def update_document_status(db: Session, document_id: str, status: str, actor: str) -> DocumentOut:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail='document not found')
    document.status = status
    log_event(db, actor, 'document.status_changed', 'document', document.id, {'status': status})
    db.commit()
    db.refresh(document)
    return serialize_document(document)
