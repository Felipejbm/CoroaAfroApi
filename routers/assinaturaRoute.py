from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import AssinaturaDB, EmpreendedorDB

router = APIRouter(prefix="/assinatura", tags=["Assinatura demonstrativa"])

PLANOS = {
    "bronze": Decimal("450.00"),
    "prata": Decimal("750.00"),
    "ouro": Decimal("1200.00"),
}


class AssinaturaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plano: Literal["bronze", "prata", "ouro"]
    forma_pagamento: Literal["cartao", "pix"]


def saida(assinatura: AssinaturaDB):
    return {
        "id": assinatura.id,
        "plano": assinatura.plano,
        "valor_mensal": float(assinatura.valor_mensal),
        "forma_pagamento": assinatura.forma_pagamento,
        "status": assinatura.status,
        "criada_em": assinatura.criada_em,
        "atualizada_em": assinatura.atualizada_em,
        "ambiente": "demonstracao",
    }


@router.get("/me")
def minha_assinatura(
    response: Response,
    db: Session = Depends(get_db),
    user: EmpreendedorDB = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"
    assinatura = db.query(AssinaturaDB).filter_by(id_empreendedor=user.id_empreendedor).first()
    return saida(assinatura) if assinatura else None


@router.post("/confirmar")
def confirmar_assinatura(
    dados: AssinaturaEntrada,
    db: Session = Depends(get_db),
    user: EmpreendedorDB = Depends(get_current_user),
):
    db.query(EmpreendedorDB).filter_by(id_empreendedor=user.id_empreendedor).with_for_update().one()
    assinatura = db.query(AssinaturaDB).filter_by(id_empreendedor=user.id_empreendedor).first()
    if assinatura:
        assinatura.plano = dados.plano
        assinatura.valor_mensal = PLANOS[dados.plano]
        assinatura.forma_pagamento = dados.forma_pagamento
        assinatura.status = "ativa"
        assinatura.atualizada_em = datetime.utcnow()
    else:
        assinatura = AssinaturaDB(
            id_empreendedor=user.id_empreendedor,
            plano=dados.plano,
            valor_mensal=PLANOS[dados.plano],
            forma_pagamento=dados.forma_pagamento,
        )
        db.add(assinatura)
    db.commit()
    db.refresh(assinatura)
    return saida(assinatura)


@router.post("/cancelar")
def cancelar_assinatura(
    db: Session = Depends(get_db),
    user: EmpreendedorDB = Depends(get_current_user),
):
    db.query(EmpreendedorDB).filter_by(id_empreendedor=user.id_empreendedor).with_for_update().one()
    assinatura = db.query(AssinaturaDB).filter_by(id_empreendedor=user.id_empreendedor).first()
    if not assinatura:
        raise HTTPException(404, "Você ainda não possui uma assinatura.")
    assinatura.status = "cancelada"
    assinatura.atualizada_em = datetime.utcnow()
    db.commit()
    db.refresh(assinatura)
    return saida(assinatura)
