from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnswerOut, QuestionIn
from app.services.rag_service import answer_question

router = APIRouter(prefix='/rag', tags=['rag'])


@router.post('/ask', response_model=AnswerOut)
def ask_question(payload: QuestionIn, db: Session = Depends(get_db)) -> AnswerOut:
    return answer_question(db, payload)
