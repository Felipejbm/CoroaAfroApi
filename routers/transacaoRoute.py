from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Transacao
from schemas import TransacoesCreate

router = APIRouter(
    prefix="/transacao",
    tags=["Transacao"]
)

@router.post('/adicionar-transacao')
def adicionar_trasacao(transacao: TransacoesCreate, db: Session = Depends(get_db)):
    nova_transacao = Transacao(
        valor = transacao.valor,
        tipo_transacao = transacao.tipo_transacao,
        data = transacao.data,
        status = transacao.status
    )

    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)

    return{
        "Msg": "Transação criada com sucesso!",
        "Empreendedor": nova_transacao
    }