import uuid

from sqlalchemy.orm import Session

from app.models import Approval, DocumentChunk, RequestRecord
from app.schemas import DraftIn, DraftOut
from app.services.audit_service import log_event
from app.services.retrieval_service import best_sentence, search_chunks


def create_draft_text(draft_type: str, instruction: str, evidence: list[tuple[DocumentChunk, float]]) -> str:
    sources = [best_sentence(chunk, instruction) for chunk, _ in evidence[:3]]
    source_block = '\n'.join(f'- {source}' for source in sources) if sources else '- 관련 문서 근거 없음. 담당자 검토 필요.'
    if draft_type == 'email':
        return f'''제목: 업무 요청 검토 및 처리 요청

안녕하세요.

아래 건에 대한 검토 및 처리를 요청드립니다.

요청 내용:
{instruction}

참고 근거:
{source_block}

검토 후 승인 가능 여부와 필요한 보완 사항을 회신 부탁드립니다.

감사합니다.'''
    if draft_type == 'report':
        return f'''# 업무 검토 보고서 초안

## 1. 목적
{instruction}

## 2. 문서 기반 근거
{source_block}

## 3. 검토 의견
현재 근거만으로 확정하기 어려운 항목은 담당 부서 확인이 필요합니다.

## 4. 요청 사항
승인자는 근거 문서의 최신 버전과 정책 적합성을 확인한 뒤 승인 또는 반려해 주세요.'''
    if draft_type == 'meeting_summary':
        return f'''# 회의록 요약 초안

## 논의 주제
{instruction}

## 관련 근거
{source_block}

## 결정 필요 사항
- 담당자 확인 필요 항목 식별
- 후속 액션 담당자 지정
- 승인 또는 반려 처리'''
    return f'''# 업무 요청서 초안

요청명: {instruction[:80]}

## 요청 배경
{instruction}

## 참고 근거
{source_block}

## 승인 조건
- 최신 사내 문서 기준 충족
- 담당 부서 검토 완료
- 감사 로그 기록 확인'''


def generate_draft_request(db: Session, payload: DraftIn) -> DraftOut:
    search_query = payload.related_question or payload.instruction
    evidence = search_chunks(db, search_query, 4)
    draft = create_draft_text(payload.draft_type, payload.instruction, evidence)
    confidence = round(sum(score for _, score in evidence[:3]) / max(1, min(3, len(evidence))), 4) if evidence else 0.0
    request = RequestRecord(
        id=str(uuid.uuid4()),
        request_type=f'draft.{payload.draft_type}',
        prompt=payload.instruction,
        response=draft,
        confidence=confidence,
        status='pending_approval',
        requester_email=payload.requester_email,
        citations=[
            {
                'document_id': chunk.document.id,
                'document_title': chunk.document.title,
                'chunk_id': chunk.id,
                'score': score,
                'sentence': best_sentence(chunk, search_query),
            }
            for chunk, score in evidence
        ],
    )
    db.add(request)
    db.flush()
    approval = Approval(id=str(uuid.uuid4()), request_id=request.id, status='pending')
    db.add(approval)
    log_event(db, payload.requester_email, 'draft.created', 'request', request.id, {'draft_type': payload.draft_type})
    db.commit()
    return DraftOut(request_id=request.id, approval_id=approval.id, draft_type=payload.draft_type, draft=draft, status=approval.status)
