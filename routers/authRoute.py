from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import LoginReq
from models import Empreendedor

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post('/login')
def logar(
    dados: LoginReq,
    db: Session = Depends(get_db)
):
    empreendedor = db.query(Empreendedor).filter(
        Empreendedor.email == dados.email
    ).first()

    if not empreendedor:
        raise HTTPException(
            status_code= 404,
            detail="Empreendedor não encontrado"
        )

    if empreendedor.senha != dados.senha:
        raise HTTPException(
            status_code= 401,
            detail= "Senha incorreta"
        )

    return{
        "Msg": "Login realizado com sucesso!",
        "Empreendedor": {
            "id": empreendedor.id_empreendedor,
            "nome": empreendedor.nome,
            "email": empreendedor.email
        }

    }