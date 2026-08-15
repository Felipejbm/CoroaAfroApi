from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import PostagemChat
from schemas import PostagemChatCreate

router = APIRouter(
    prefix="/postagem",
    tags=["Postagem"]
)

@router.post('/criar-postagem')
def criar_postagem(postagem: PostagemChatCreate, db: Session = Depends(get_db)):
    nova_postagem = PostagemChat(
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