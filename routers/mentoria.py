from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database import get_db
from models import MentorDB, MentoriaDB, EmpreendedorDB, EmpresaDB, EmpresaEmpreendedorDB
from security import get_current_mentor

router = APIRouter(prefix="/mentoria", tags=["Mentoria"])


def resumo(db, user):
    link = db.get(EmpresaEmpreendedorDB, user.id_empreendedor)
    empresa = db.get(EmpresaDB, link.id_empresa) if link else None
    return {"id": user.id_empreendedor, "nome": user.nome,
            "empresa": empresa.nome if empresa else None}


@router.get("/mentorados")
def mentorados(response: Response, mentor: MentorDB = Depends(get_current_mentor), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    users = db.query(EmpreendedorDB).join(MentoriaDB,
        MentoriaDB.id_empreendedor == EmpreendedorDB.id_empreendedor).filter(
            MentoriaDB.id_mentor == mentor.id_mentor, MentoriaDB.ativo.is_(True)).all()
    return [resumo(db, user) for user in users]


@router.get("/mentorados/{id_empreendedor}")
def detalhes(id_empreendedor: int, response: Response,
             mentor: MentorDB = Depends(get_current_mentor), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    link = db.get(MentoriaDB, (mentor.id_mentor, id_empreendedor))
    user = db.get(EmpreendedorDB, id_empreendedor) if link and link.ativo else None
    if not user:
        raise HTTPException(404, "Mentorado não encontrado para este mentor.")
    return resumo(db, user)

