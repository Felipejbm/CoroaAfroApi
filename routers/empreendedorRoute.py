from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from models import EmpreendedorDB
from schemas.EmpreendedorSchema.EmpreendedorSchema import EmpreendedorAtualizar, EmpreendedorCreate
from security import (
    hash_password,
    validate_origin
)
from dependencies import (
    get_current_user
)
from schemas.AuthSchema.AuthSchema import MentorPublic, EmpreendedorPublic
from services.company_identity import usuario_vinculado
from services.foto_perfil import LIMITE_FOTO, normalizar_foto

router = APIRouter(prefix="/empreendedor", tags=["Empreendedor"])


def saida(user: EmpreendedorDB):
    dados_publicos = EmpreendedorPublic.model_validate(user)

    return {
        **dados_publicos.model_dump(), 
        "id_empreendedor": user.id_empreendedor
        }


@router.post("", status_code=201, dependencies=[Depends(validate_origin)])
def criar_empreendedor(dados: EmpreendedorCreate, db: Session = Depends(get_db)):
    if not dados.nome.strip() or not dados.email.strip() or not dados.senha or not dados.telefone.strip():
        raise HTTPException(422, "Preencha nome, e-mail, senha e telefone.")
    novo = EmpreendedorDB(nome=dados.nome.strip(), email=dados.email.strip(),
                         senha=hash_password(dados.senha), telefone=dados.telefone.strip())
    db.add(novo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma conta com esse e-mail.")
    db.refresh(novo)
    return {"Msg": "Empreendedor criado com sucesso!", "Empreendedor": saida(novo)}


@router.get("")
def listar_empreendedores(user: EmpreendedorDB = Depends(get_current_user)):
    return [saida(user)]


@router.get("/me/foto")
def obter_foto(user: EmpreendedorDB = Depends(get_current_user)):
    if not user.foto_perfil:
        raise HTTPException(404, "Você ainda não adicionou uma foto de perfil.")
    return Response(user.foto_perfil, media_type="image/jpeg", headers={
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.put("/me/foto", response_model=EmpreendedorPublic)
def salvar_foto(response: Response, foto: UploadFile = File(...),
                db: Session = Depends(get_db),
                user: EmpreendedorDB = Depends(get_current_user)):
    try:
        conteudo = foto.file.read(LIMITE_FOTO + 1)
        user.foto_perfil = normalizar_foto(conteudo, foto.content_type)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    finally:
        foto.file.close()
    response.headers["Cache-Control"] = "no-store"
    return EmpreendedorPublic.model_validate(user)


@router.get("/{id_empreendedor}")
def obter_empreendedor_por_id(id_empreendedor: int, user: EmpreendedorDB = Depends(get_current_user)):
    if id_empreendedor != user.id_empreendedor:
        raise HTTPException(404, "Empreendedor não encontrado.")
    return saida(user)


@router.patch("/{id_empreendedor}")
def atualizar_empreendedor(id_empreendedor: int, dados: EmpreendedorAtualizar,
                           db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    obter_empreendedor_por_id(id_empreendedor, user)
    usuario = usuario_vinculado(db, user)
    limits = {"nome": 150 if usuario else 255, "email": 150 if usuario else 255, "telefone": 20}
    for key, value in dados.model_dump(exclude_unset=True).items():
        if value is None or not value.strip() or len(value.strip()) > limits[key]:
            raise HTTPException(422, f"Campo inválido: {key}.")
        setattr(user, key, value.strip())
        if usuario:
            setattr(usuario, key, value.strip())
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma conta com esse e-mail.")
    db.refresh(user)
    return saida(user)
