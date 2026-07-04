from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.demo_service import seed_demo

router = APIRouter(prefix='/demo', tags=['demo'])


@router.post('/seed')
def seed(db: Session = Depends(get_db)) -> dict:
    return seed_demo(db)
