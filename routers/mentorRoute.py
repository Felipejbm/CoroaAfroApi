from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Mentor
from schemas import MentorCreate

router = APIRouter(
    prefix="/mentor",
    tags=["Mentor"]
)

@router.post('/criar-mentor')
def criar_mentor(mentor: MentorCreate, db: Session = Depends(get_db)):
    novo_mentor = Mentor(
        nome = mentor.nome,
        especialidade = mentor.especialidade,
        biografia = mentor.biografia
    )

    db.add(novo_mentor)
    db.commit()
    db.refresh(novo_mentor)

    return{
        "Msg": "Mentor criado com sucesso!",
        "Empreendedor": novo_mentor
    }