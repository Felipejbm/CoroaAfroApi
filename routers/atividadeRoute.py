from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Atividade
from schemas import AtividadeCreate

router = APIRouter(
    prefix="/atividade",
    tags=["Atividade"],
)

@router.post('/criar-atividade')
def criar_atividade(atividade: AtividadeCreate, db: Session = Depends(get_db)):
    nova_atividade = Atividade(
        titulo_tarefa = atividade.titulo_tarefa,
        conteudo = atividade.conteudo
    )

    db.add(nova_atividade)
    db.commit()
    db.refresh(nova_atividade)

    return{
        "Msg": "Atividade criada com sucesso!",
        "Empreendedor": nova_atividade
    }