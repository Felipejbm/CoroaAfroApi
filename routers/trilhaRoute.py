from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Trilha
from schemas import TrilhaCreate

router = APIRouter(
    prefix="/trilha",
    tags=["Trilha"]
)


@router.post('/criar-trilha')
def criar_trilha(trilha: TrilhaCreate, db: Session = Depends(get_db)):
    nova_trilha = Trilha(
        titulo = trilha.titulo,
        tipo_trilha = trilha.tipo_trilha
    )

    db.add(nova_trilha)
    db.commit()
    db.refresh(nova_trilha)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_trilha
    }