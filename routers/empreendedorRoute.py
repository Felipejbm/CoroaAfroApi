from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import EmpreendedorDB
from schemas.database.schemas import EmpreendedorCreate
from schemas.EmpreendedorSchema.EmpreendedorSchema import (
    EmpreendedorPorIdResponse,
    EmpreendedorAtualizarResponse,
    EmpreendedorAtualizar
    )

router = APIRouter(
    prefix="/empreendedor",
    tags=["Empreendedor"]
)

@router.post('')
def criar_empreendedor(empreendedor: EmpreendedorCreate, db: Session = Depends(get_db)):
    novo_empreendedor = EmpreendedorDB(
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

@router.get('')
def litar_empreendedores(db: Session = Depends(get_db)):
    empreendedores_banco = db.query(EmpreendedorDB).all()

    return empreendedores_banco

@router.get('/{id_empreendedor}', response_model=EmpreendedorPorIdResponse)
def obter_empreendedor_por_id(id_empreendedor: int, db: Session = Depends(get_db)):
    empreendedor_banco = db.query(EmpreendedorDB).filter(EmpreendedorDB.id_empreendedor == id_empreendedor).first()

    if not empreendedor_banco:
        raise HTTPException(status_code=404, detail="Empreendedor não encontrada")
    return  empreendedor_banco

@router.patch('/{id_empreendedor}', response_model=EmpreendedorAtualizarResponse)
def atualizar_empreendedor(
        id_empreendedor: int, 
        empreendedor_data: EmpreendedorAtualizar,
        db: Session = Depends(get_db) 
        ):
    empreendedor_banco = db.query(EmpreendedorDB).filter(EmpreendedorDB.id_empreendedor == id_empreendedor).first()

    if not empreendedor_banco:
        raise HTTPException(status_code=404, detail=("Empreendedor não encontrada"))

    empreendedor_atualizado = empreendedor_data.model_dump(exclude_unset=True)

    for chave, valor in empreendedor_atualizado.items():
        setattr(empreendedor_banco, chave, valor)

    db.commit()
    db.refresh(empreendedor_banco)

    return empreendedor_banco

@router.delete('/{id_empreendedor}')
def deletar_empreendedor(id_empreendedor: int, db: Session = Depends(get_db)):
    empreendedor_banco = db.query(EmpreendedorDB).filter(EmpreendedorDB.id_empreendedor == id_empreendedor). first()

    if not empreendedor_banco:
        raise HTTPException(status_code=404, detail="Empreendedor não encontrada")

    db.delete(empreendedor_banco)
    db.commit()

    return "Empreendedor deletado com sucesso"