from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import MentorDB
from schemas.common import MentorCreate
from schemas.mentor import (
    MentorPorIdResponse,
    MentorAtualizarResponse,
    MentorAtualizar
)

router = APIRouter(
    prefix="/mentor",
    tags=["Mentor"]
)

@router.post('/criar-mentor')
def criar_mentor(mentor: MentorCreate, db: Session = Depends(get_db)):
    novo_mentor = MentorDB(
        nome = mentor.nome,
        especialidade = mentor.especialidade,
        biografia = mentor.biografia
    )

    db.add(novo_mentor)
    db.commit()
    db.refresh(novo_mentor)

    return{
        "Msg": "Mentor criado com sucesso!",
        "Empreendedor": novo_mentor
    }

@router.get('')
def listar_mentores(db: Session = Depends(get_db)):
    mentores_banco = db.query(MentorDB).all()

    return mentores_banco

@router.get('/{id_mentor}', response_model=MentorPorIdResponse)
def obter_mentor_por_id(id_mentor: int, db: Session = Depends(get_db)):
    mentor_banco = db.query(MentorDB).filter(MentorDB.id_mentor == id_mentor).first()

    if not mentor_banco:
        raise HTTPException(status_code=404, detail="Mentor não encontrada")
    return  mentor_banco

@router.patch('/{id_mentor}', response_model=MentorAtualizarResponse)
def atualizar_mentor(
        id_mentor: int, 
        mentor_data: MentorAtualizar,
        db: Session = Depends(get_db) 
        ):
    mentor_banco = db.query(MentorDB).filter(MentorDB.id_mentor == id_mentor).first()

    if not mentor_banco:
        raise HTTPException(status_code=404, detail=("Mentor não encontrada"))

    mentor_atualizada = mentor_data.model_dump(exclude_unset=True)

    for chave, valor in mentor_atualizada.items():
        setattr(mentor_banco, chave, valor)

    db.commit()
    db.refresh(mentor_banco)

    return mentor_banco

@router.delete('/{id_mentor}')
def deletar_mentor(id_mentor: int, db: Session = Depends(get_db)):
    mentor_banco = db.query(MentorDB).filter(MentorDB.id_mentor == id_mentor). first()

    if not mentor_banco:
        raise HTTPException(status_code=404, detail="Mentor não encontrada")

    db.delete(mentor_banco)
    db.commit()

    return "Mentor deletada com sucesso"
