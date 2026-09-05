from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AtividadeDB
from schemas.AtividadeSchema.AtividadeSchema import (
    AtividadePorIdResponse, 
    AtividadeAtualizarResponse, 
    AtividadeAtualizar,
    AtividadeCreate
    )

router = APIRouter(
    prefix="/atividade",
    tags=["Atividade"],
)

@router.get('')
def listar_atividades(db: Session = Depends(get_db)):
    atividades_banco = db.query(AtividadeDB).all()

    return atividades_banco

@router.get('/{id_atividade}', response_model=AtividadePorIdResponse)
def obter_atividade_por_id(id_atividade: int, db: Session = Depends(get_db)):
    atividade_banco = db.query(AtividadeDB).filter(AtividadeDB.id_atividade == id_atividade).first()

    if not atividade_banco:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    return  atividade_banco

@router.post('')
def criar_atividade(atividade: AtividadeCreate, db: Session = Depends(get_db)):
    nova_atividade = AtividadeDB(
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

@router.patch('/{id_atividade}', response_model=AtividadeAtualizarResponse)
def atualizar_atividade(
        id_atividade: int, 
        atividade_data: AtividadeAtualizar,
        db: Session = Depends(get_db) 
        ):
    atividade_banco = db.query(AtividadeDB).filter(AtividadeDB.id_atividade == id_atividade).first()

    if not atividade_banco:
        raise HTTPException(status_code=404, detail=("Atividade não encontrada"))

    atividade_atualizada = atividade_data.model_dump(exclude_unset=True)

    for chave, valor in atividade_atualizada.items():
        setattr(atividade_banco, chave, valor)

    db.commit()
    db.refresh(atividade_banco)

    return atividade_banco

@router.delete('/{id_atividade}')
def deletar_atividade(id_atividade: int, db: Session = Depends(get_db)):
    atividade_banco = db.query(AtividadeDB).filter(AtividadeDB.id_atividade == id_atividade). first()

    if not atividade_banco:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")

    db.delete(atividade_banco)
    db.commit()

    return "Atividade deletada com sucesso"