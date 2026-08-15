from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Empreendedor
from schemas import EmpreendedorCreate

router = APIRouter(
    prefix="/empreendedor",
    tags=["Empreendedor"]
)

@router.post('/criar-empreendedor')
def criar_empreendedor(empreendedor: EmpreendedorCreate, db: Session = Depends(get_db)):
    novo_empreendedor = Empreendedor(
        nome = empreendedor.nome,
        email = empreendedor.email,
        senha = empreendedor.senha,
        telefone = empreendedor.telefone,
    )

    db.add(novo_empreendedor)
    db.commit()
    db.refresh(novo_empreendedor)

    return{
        "Msg": "Empreendedor criado com sucesso!",
        "Empreendedor": novo_empreendedor
    }