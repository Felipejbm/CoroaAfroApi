from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TransacaoDB
from schemas.database.schemas import TransacoesCreate
from schemas.TransacaoSchema.TransacaoSchema import (
    TransacaoPorIdResponse,
    TransacaoAtualizarResponse,
    TransacaoAtualizar
)

router = APIRouter(
    prefix="/transacao",
    tags=["Transacao"]
)

@router.post('/adicionar-transacao')
def adicionar_trasacao(transacao: TransacoesCreate, db: Session = Depends(get_db)):
    nova_transacao = TransacaoDB(
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

@router.get('/{id_transacao}', response_model=TransacaoPorIdResponse)
def obter_transacao_por_id(id_transacao: int, db: Session = Depends(get_db)):
    transacao_banco = db.query(TransacaoDB).filter(TransacaoDB.id_transacao == id_transacao).first()

    if not transacao_banco:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return  transacao_banco

@router.patch('/{id_transacao}', response_model=TransacaoPorIdResponse)
def atualizar_transacao(
        id_transacao: int, 
        transacao_data: TransacaoAtualizar,
        db: Session = Depends(get_db) 
        ):
    transacao_banco = db.query(TransacaoDB).filter(TransacaoDB.id_transacao == id_transacao).first()

    if not transacao_banco:
        raise HTTPException(status_code=404, detail=("Transação não encontrada"))

    transacao_atualizada = transacao_data.model_dump(exclude_unset=True)

    for chave, valor in transacao_atualizada.items():
        setattr(transacao_banco, chave, valor)

    db.commit()
    db.refresh(transacao_banco)

    return transacao_banco

@router.delete('/{id_transacao}')
def deletar_transacao(id_transacao: int, db: Session = Depends(get_db)):
    transacao_banco = db.query(TransacaoDB).filter(TransacaoDB.id_transacao == id_transacao). first()

    if not transacao_banco:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    db.delete(transacao_banco)
    db.commit()

    return "Transação deletada com sucesso"