from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SaldoDB
from schemas.common import SaldoCreate
from schemas.saldo import (
    SaldoPorIdResponse,
    SaldoAtualizarResponse,
    SaldoAtualizar
)

router = APIRouter(
    prefix="/saldo",
    tags=["Saldo"]
)

@router.post('/adicionar-saldo')
def adicionar_saldo(saldo: SaldoCreate, db: Session = Depends(get_db)):
    novo_saldo = SaldoDB(
        saldo = saldo.saldo,
        meta_faturamento = saldo.meta_faturamento,
        data = saldo.data,
        total_entradas = saldo.total_entradas,
        total_saidas = saldo.total_saidas,
        valor_inicial = saldo.valor_inicial,
        saldo_final =  saldo.saldo_final
    )

    db.add(novo_saldo)
    db.commit()
    db.refresh(novo_saldo)

    return{
        "Msg": "Saldo criado com sucesso!",
        "Empreendedor": novo_saldo
    }

@router.get('/{id_saldo}', response_model=SaldoPorIdResponse)
def obter_saldo_por_id(id_saldo: int, db: Session = Depends(get_db)):
    saldo_banco = db.query(SaldoDB).filter(SaldoDB.id_saldo == id_saldo).first()

    if not saldo_banco:
        raise HTTPException(status_code=404, detail="Saldo não encontrada")
    return  saldo_banco

@router.patch('/{id_saldo}', response_model=SaldoAtualizarResponse)
def atualizar_saldo(
        id_saldo: int, 
        saldo_data: SaldoAtualizar,
        db: Session = Depends(get_db) 
        ):
    saldo_banco = db.query(SaldoDB).filter(SaldoDB.id_saldo == id_saldo).first()

    if not saldo_banco:
        raise HTTPException(status_code=404, detail=("Saldo não encontrada"))

    saldo_atualizado = saldo_data.model_dump(exclude_unset=True)

    for chave, valor in saldo_atualizado.items():
        setattr(saldo_banco, chave, valor)

    db.commit()
    db.refresh(saldo_banco)

    return saldo_banco

@router.delete('/{id_saldo}')
def deletar_saldo(id_saldo: int, db: Session = Depends(get_db)):
    saldo_banco = db.query(SaldoDB).filter(SaldoDB.id_saldo == id_saldo). first()

    if not saldo_banco:
        raise HTTPException(status_code=404, detail="Saldo não encontrada")

    db.delete(saldo_banco)
    db.commit()

    return "Saldo deletada com sucesso"
