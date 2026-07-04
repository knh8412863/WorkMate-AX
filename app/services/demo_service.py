import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.models import Document, DocumentChunk
from app.services.audit_service import log_event
from app.utils.text import chunk_text, to_term_vector, tokenize


def seed_demo(db: Session) -> dict:
    existing = db.scalar(select(Document).where(Document.title == '재택근무 운영 규정'))
    if existing:
        return {'status': 'already_seeded', 'document_id': existing.id}

    sample = '''재택근무 운영 규정

재택근무는 팀 리더의 사전 승인을 받아 주 2회까지 사용할 수 있다. 긴급한 개인 사정이 있는 경우 인사팀과 소속 부서장이 예외를 승인할 수 있다.

보안 자료를 취급하는 임직원은 회사 VPN과 다중 인증을 사용해야 하며, 개인 저장소에 문서를 보관할 수 없다.

회의록은 회의 종료 후 24시간 이내에 참석자, 결정 사항, 후속 조치 담당자를 포함하여 등록해야 한다.

계약서 검토 요청은 법무팀 승인 전 외부 발송이 금지된다. 계약 금액, 계약 기간, 개인정보 처리 조항이 포함된 경우 반드시 법무팀과 보안팀 검토를 거친다.'''
    document = Document(
        id=str(uuid.uuid4()),
        title='재택근무 운영 규정',
        category='policy',
        version=1,
        file_name='remote-work-policy.md',
        file_path=str(UPLOAD_DIR / 'remote-work-policy.md'),
        uploaded_by='admin@company.com',
    )
    Path(document.file_path).write_text(sample, encoding='utf-8')
    document.chunks = [
        DocumentChunk(chunk_index=index, content=chunk, token_count=len(tokenize(chunk)), term_vector=to_term_vector(chunk))
        for index, chunk in enumerate(chunk_text(sample))
    ]
    db.add(document)
    log_event(db, 'admin@company.com', 'demo.seeded', 'document', document.id, {'title': document.title})
    db.commit()
    return {'status': 'seeded', 'document_id': document.id}
