# WorkMate AX

사내 문서 기반 업무지원 RAG와 승인 워크플로우를 결합한 FastAPI 서비스입니다. 
규정, 매뉴얼, 회의록, FAQ, 계약서 같은 내부 문서를 업로드하면 문서를 chunking하고 검색 인덱스를 만든 뒤 질문에 답변합니다. 이메일, 보고서, 회의록 요약, 업무 요청서 초안은 사람이 승인해야 최종 처리되도록 설계했습니다.

## 핵심 기능

- PDF, TXT, MD 문서 업로드
- 문서 chunking 및 로컬 vector-like 검색
- 질문 답변과 출처 문장 표시
- 낮은 신뢰도 답변에 `확인 필요` 표시
- 이메일, 보고서, 회의록 요약, 업무 요청서 초안 생성
- 사용자 승인/반려 플로우
- 요청 이력, 답변 이력, 감사 로그 저장
- 관리자용 문서 버전 및 상태 관리


## 실행 화면

### 문서 업로드 결과

사내 문서를 업로드하면 파일명, 문서 제목, 버전, 상태, chunk 개수가 저장됩니다. 동일 제목의 문서를 다시 업로드하면 문서 버전이 증가합니다.

![문서 업로드 결과](docs/images/문서%20업로드%20결과.png)

### RAG 문서 근거 기반 답변

질문에 대해 업로드된 문서 chunk를 검색하고, 답변과 함께 신뢰도 및 출처 문장을 반환합니다. 신뢰도가 낮은 경우 `확인 필요` 상태로 표시됩니다.

![RAG 문서 근거 기반 답변](docs/images/rag_문서%20근거%20기반%20답변.png)

### 승인 워크플로우

이메일, 보고서, 회의록 요약, 업무 요청서 초안은 바로 최종 처리하지 않고 승인 대기 상태로 생성됩니다. 승인자는 내용을 검토한 뒤 승인 또는 반려할 수 있습니다.

![승인 워크플로우](docs/images/승인%20워크플로우.png)

## 기술 스택

- Backend: FastAPI, Pydantic, SQLAlchemy
- DB: SQLite
- Retrieval: TF-IDF cosine similarity 기반 로컬 검색
- Document parsing: pypdf, plain text parser

현재 구현은 외부 API 없이 동작합니다. 

## 실행 방법

```bash
cd /Users/admin/WorkMate_AX
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m uvicorn app.main:app --reload
```

8000번 포트가 이미 사용 중이면 아래처럼 다른 포트를 지정합니다.

```bash
python3 -m uvicorn app.main:app --reload --port 8001
```

API 문서는 실행 후 아래에서 확인합니다.

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## 빠른 시연

데모 문서를 먼저 넣습니다.

```bash
curl -X POST http://127.0.0.1:8000/demo/seed
```

문서 기반 질문을 합니다.

```bash
curl -X POST http://127.0.0.1:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"재택근무는 주 몇 회까지 가능한가요?","requester_email":"user@company.com"}'
```

이메일 초안을 생성합니다. 초안은 바로 발송되지 않고 승인 대기 상태가 됩니다.

```bash
curl -X POST http://127.0.0.1:8000/drafts \
  -H "Content-Type: application/json" \
  -d '{"draft_type":"email","instruction":"법무팀에 계약서 외부 발송 가능 여부 검토를 요청해줘","requester_email":"user@company.com"}'
```

승인 목록을 확인합니다.

```bash
curl http://127.0.0.1:8000/approvals
```

승인합니다.

```bash
curl -X POST http://127.0.0.1:8000/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_email":"manager@company.com","comment":"근거 확인 완료"}'
```

반려할 때는 `/reject`를 사용합니다.

## 주요 API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/health` | 서비스 상태 확인 |
| POST | `/documents` | 문서 업로드 및 chunking/indexing |
| GET | `/documents` | 문서 목록 조회 |
| PATCH | `/admin/documents/{document_id}/status` | 문서 활성/보관/비활성 처리 |
| POST | `/rag/ask` | RAG 질문 답변 |
| POST | `/drafts` | 이메일/보고서/회의록/업무요청서 초안 생성 |
| GET | `/approvals` | 승인 대기 및 처리 이력 조회 |
| POST | `/approvals/{approval_id}/approve` | 초안 승인 |
| POST | `/approvals/{approval_id}/reject` | 초안 반려 |
| GET | `/history` | 요청 및 답변 이력 조회 |
| GET | `/audit-logs` | 감사 로그 조회 |
| POST | `/demo/seed` | 데모 문서 등록 |

## 데이터 모델

- `documents`: 업로드 문서의 제목, 카테고리, 버전, 상태, 파일 경로
- `document_chunks`: 검색 대상 chunk와 term vector
- `requests`: 질문/초안 생성 요청, 응답, 신뢰도, 상태
- `approvals`: 승인/반려 상태, 승인자, 최종 payload
- `audit_logs`: 문서 업로드, 질문, 초안 생성, 승인/반려 이벤트

## 설계 포인트

이 서비스는 단순 챗봇이 아니라 업무 흐름을 다룹니다. 
RAG 답변은 출처와 신뢰도를 함께 제공하고, 실제 업무 처리로 이어지는 이메일/보고서/요청서 초안은 승인 전까지 `pending_approval` 상태로 남습니다. 
모든 주요 액션은 감사 로그에 남기 때문에 기업형 AX 서비스의 통제, 추적성, 사람 검토 요구사항을 보여줄 수 있습니다.

## 운영 확장 아이디어

- SQLite를 PostgreSQL + pgvector로 교체
- `to_term_vector`를 embedding API 호출로 교체
- 문서별 권한 ACL과 부서별 접근 제어 추가
- SSO/OAuth2 로그인 및 역할 기반 권한 관리 추가
- 승인 단계 다중화: 팀장, 법무, 보안, 재무
- 실제 이메일/그룹웨어/Slack/Jira 연동
- 문서 변경 시 기존 답변 영향도 분석
- React 관리자 화면 추가

## 프로젝트 구조

```text
WorkMate_AX/
├── app/
│   ├── main.py              # FastAPI 앱 생성, CORS, 라우터 등록
│   ├── config.py            # 데이터/업로드/DB 경로 설정
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models.py            # DB 테이블 모델
│   ├── schemas.py           # 요청/응답 Pydantic 스키마
│   ├── routers/             # API endpoint 계층
│   │   ├── admin.py
│   │   ├── approvals.py
│   │   ├── demo.py
│   │   ├── documents.py
│   │   ├── drafts.py
│   │   ├── history.py
│   │   └── rag.py
│   ├── services/            # 비즈니스 로직 계층
│   │   ├── approval_service.py
│   │   ├── audit_service.py
│   │   ├── demo_service.py
│   │   ├── document_service.py
│   │   ├── draft_service.py
│   │   ├── history_service.py
│   │   ├── rag_service.py
│   │   └── retrieval_service.py
│   └── utils/
│       └── text.py          # tokenize, chunking, similarity 유틸
├── main.py                  # 호환용 얇은 진입점
├── pyproject.toml           # Python 패키지 및 의존성
├── README.md                # 실행 및 API 설명
└── data/                    # 실행 중 생성되는 SQLite DB와 업로드 파일
```

### 계층 분리 기준

- `routers/`: HTTP 요청/응답과 FastAPI dependency만 담당합니다.
- `services/`: 문서 처리, RAG, 초안 생성, 승인, 감사 로그 같은 업무 로직을 담당합니다.
- `models.py`: DB 테이블 구조만 정의합니다.
- `schemas.py`: API 입출력 데이터 모양만 정의합니다.
- `utils/`: DB나 FastAPI에 의존하지 않는 순수 텍스트 처리 함수를 둡니다.
