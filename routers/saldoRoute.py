from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Saldo
from schemas import SaldoCreate

router = APIRouter(
    prefix="/saldo",
    tags=["Saldo"]
)

@router.post('/adicionar-saldo')
def adicionar_saldo(saldo: SaldoCreate, db: Session = Depends(get_db)):
    novo_saldo = Saldo(
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