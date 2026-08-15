from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import MensagemChat
from schemas import MensagemChatCreate

router = APIRouter(
    prefix="/mensagem",
    tags=["Mensagem"]
)

@router.post('/criar-mensagem')
def criar_mensagem(mensagem: MensagemChatCreate, db: Session = Depends(get_db)):
    nova_mensagem = MensagemChat(
        texto_mensagem = mensagem.texto_mensagem,
        data_envio = mensagem.data_envio,
        lida = mensagem.lida,
        remetente = mensagem.remetente
    )

    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)

    return{
        "Msg": "Mensagem criada com sucesso!",
        "Empreendedor": nova_mensagem
    }