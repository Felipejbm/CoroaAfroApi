from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import PostagemChatDB
from schemas.database.schemas import PostagemChatCreate
from schemas.PostagemSchema.PostagemSchema import (
    PostagemPorIdResponse,
    PostagemAtualizarResponse,
    PostagemAtualizar
)


router = APIRouter(
    prefix="/postagem",
    tags=["Postagem"]
)

@router.post('/criar-postagem')
def criar_postagem(postagem: PostagemChatCreate, db: Session = Depends(get_db)):
    nova_postagem = PostagemChatDB(
       conteudo_texto = postagem.conteudo_texto,
       midia_url = postagem.midia_url,
       data_publicacao = postagem.data_publicacao
    )

    db.add(nova_postagem)
    db.commit()
    db.refresh(nova_postagem)

    return{
        "Msg": "Postagem criada com sucesso!",
        "Empreendedor": nova_postagem
    }

@router.get('')
def listar_postagens(db: Session = Depends(get_db)):
    postagem_banco = db.query(PostagemChatDB).all()

    return postagem_banco

@router.get('/{id_post}', response_model=PostagemPorIdResponse)
def obter_postagem_por_id(id_post: int, db: Session = Depends(get_db)):
    postagem_banco = db.query(PostagemChatDB).filter(PostagemChatDB.id_post == id_post).first()

    if not postagem_banco:
        raise HTTPException(status_code=404, detail="Postagem não encontrada")
    return  postagem_banco

@router.patch('/{id_post}', response_model=PostagemAtualizarResponse)
def atualizar_postagem(
        id_post: int, 
        postagem_data: PostagemAtualizar,
        db: Session = Depends(get_db) 
        ):
    postagem_banco = db.query(PostagemChatDB).filter(PostagemChatDB.id_post == id_post).first()

    if not postagem_banco:
        raise HTTPException(status_code=404, detail=("Postagem não encontrada"))

    postagem_atualizada = postagem_data.model_dump(exclude_unset=True)

    for chave, valor in postagem_atualizada.items():
        setattr(postagem_banco, chave, valor)

    db.commit()
    db.refresh(postagem_banco)

    return postagem_banco

@router.delete('/{id_post}')
def deletar_postagem(id_post: int, db: Session = Depends(get_db)):
    postagem_banco = db.query(PostagemChatDB).filter(PostagemChatDB.id_post == id_post). first()

    if not postagem_banco:
        raise HTTPException(status_code=404, detail="Postagem não encontrada")

    db.delete(postagem_banco)
    db.commit()

    return "Postagem deletada com sucesso"