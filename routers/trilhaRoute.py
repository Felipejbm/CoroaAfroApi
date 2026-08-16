from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TrilhaDB
from schemas.database.schemas import TrilhaCreate
from schemas.TrilhaSchema.TrilhaSchema import (
    TrilhaPorIdResponse,
    TrilhaAtualizarResponse,
    TrilhaAtualizar
)

router = APIRouter(
    prefix="/trilha",
    tags=["Trilha"]
)


@router.post('/criar-trilha')
def criar_trilha(trilha: TrilhaCreate, db: Session = Depends(get_db)):
    nova_trilha = TrilhaDB(
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

@router.get('')
def listar_trilhas(db: Session = Depends(get_db)):
    trilhas_banco = db.query(TrilhaDB).all()

    return trilhas_banco

@router.get('/{id_trilha}', response_model=TrilhaPorIdResponse)
def obter_trilha_por_id(id_trilha: int, db: Session = Depends(get_db)):
    trilha_banco = db.query(TrilhaDB).filter(TrilhaDB.id_trilha == id_trilha).first()

    if not trilha_banco:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")
    return  trilha_banco

@router.patch('/{id_trilha}', response_model=TrilhaAtualizarResponse)
def atualizar_trilha(
        id_trilha: int, 
        trilha_data: TrilhaAtualizar,
        db: Session = Depends(get_db) 
        ):
    trilha_banco = db.query(TrilhaDB).filter(TrilhaDB.id_trilha == id_trilha).first()

    if not trilha_banco:
        raise HTTPException(status_code=404, detail=("Trilha não encontrada"))

    trilha_atualizada = trilha_data.model_dump(exclude_unset=True)

    for chave, valor in trilha_atualizada.items():
        setattr(trilha_banco, chave, valor)

    db.commit()
    db.refresh(trilha_banco)

    return trilha_banco

@router.delete('/{id_trilha}')
def deletar_trilha(id_trilha: int, db: Session = Depends(get_db)):
    trilha_banco = db.query(TrilhaDB).filter(TrilhaDB.id_trilha == id_trilha). first()

    if not trilha_banco:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")

    db.delete(trilha_banco)
    db.commit()

    return "Trilha deletada com sucesso"