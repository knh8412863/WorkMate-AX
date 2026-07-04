from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - registers SQLAlchemy models
from app.database import Base, engine
from app.routers import admin, approvals, demo, documents, drafts, history, rag


def create_app() -> FastAPI:
    api = FastAPI(
        title='WorkMate AX',
        description='사내 문서 기반 RAG + 사람 승인 워크플로우 업무지원 API',
        version='0.1.0',
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    api.include_router(documents.router)
    api.include_router(admin.router)
    api.include_router(rag.router)
    api.include_router(drafts.router)
    api.include_router(approvals.router)
    api.include_router(history.router)
    api.include_router(demo.router)

    @api.on_event('startup')
    def startup() -> None:
        Base.metadata.create_all(bind=engine)

    @api.get('/health', tags=['health'])
    def health() -> dict[str, str]:
        return {'status': 'ok', 'service': 'workmate-ax'}

    return api


app = create_app()
