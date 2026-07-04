import math
import re
from collections import Counter

STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was', 'were', 'have', 'has', 'shall',
    '및', '또는', '그리고', '합니다', '있는', '대한', '으로', '에서', '에게', '이다', '한다', '관련', '경우',
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r'[A-Za-z0-9가-힣]{2,}', text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def to_term_vector(text: str) -> dict[str, float]:
    counts = Counter(tokenize(text))
    total = sum(counts.values()) or 1
    return {term: count / total for term, count in counts.items()}


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    common = set(left) & set(right)
    dot = sum(left[key] * right[key] for key in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?。！？])\s+|\n+', text.strip())
    return [part.strip() for part in parts if part.strip()]


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    normalized = re.sub(r'\s+', ' ', text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind('.', start, end)
            if boundary > start + max_chars // 2:
                end = boundary + 1
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
