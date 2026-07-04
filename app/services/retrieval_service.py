from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.schemas import CitationOut
from app.utils.text import cosine_similarity, split_sentences, to_term_vector


def search_chunks(db: Session, query: str, top_k: int) -> list[tuple[DocumentChunk, float]]:
    query_vector = to_term_vector(query)
    chunks = db.scalars(select(DocumentChunk).join(Document).where(Document.status == 'active')).all()
    scored = [(chunk, cosine_similarity(query_vector, chunk.term_vector or {})) for chunk in chunks]
    return [(chunk, score) for chunk, score in sorted(scored, key=lambda item: item[1], reverse=True)[:top_k] if score > 0]


def best_sentence(chunk: DocumentChunk, query: str) -> str:
    query_vector = to_term_vector(query)
    sentences = split_sentences(chunk.content)
    if not sentences:
        return chunk.content[:280]
    return max(sentences, key=lambda sentence: cosine_similarity(query_vector, to_term_vector(sentence)))[:500]


def build_answer(question: str, results: list[tuple[DocumentChunk, float]]) -> tuple[str, float, list[CitationOut]]:
    if not results:
        return (
            '등록된 문서에서 직접 근거를 찾지 못했습니다. 담당자 확인 후 답변하거나 관련 문서를 추가 업로드해 주세요.',
            0.0,
            [],
        )

    citations: list[CitationOut] = []
    evidence_lines: list[str] = []
    for chunk, score in results:
        sentence = best_sentence(chunk, question)
        evidence_lines.append(f'- {sentence}')
        citations.append(
            CitationOut(
                document_id=chunk.document.id,
                document_title=chunk.document.title,
                version=chunk.document.version,
                chunk_id=chunk.id,
                sentence=sentence,
                score=round(score, 4),
            )
        )

    confidence = min(0.98, round(sum(score for _, score in results[:3]) / max(1, min(3, len(results))) * 8.0, 4))
    prefix = '확인 필요: ' if confidence < 0.45 else ''
    answer = (
        f'{prefix}문서 검색 결과를 기준으로 답변합니다.\n\n'
        f'질문: {question}\n\n'
        '핵심 근거:\n'
        + '\n'.join(evidence_lines[:4])
        + '\n\n실무 처리 시 최신 문서 버전과 담당 부서 승인 여부를 함께 확인하세요.'
    )
    return answer, confidence, citations
