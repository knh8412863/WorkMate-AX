from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DraftIn, DraftOut
from app.services.draft_service import generate_draft_request

router = APIRouter(prefix='/drafts', tags=['drafts'])


@router.post('', response_model=DraftOut)
def generate_draft(payload: DraftIn, db: Session = Depends(get_db)) -> DraftOut:
    return generate_draft_request(db, payload)
