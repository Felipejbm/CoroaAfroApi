from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import MensagemChatDB
from schemas.database.schemas import MensagemChatCreate
from schemas.MensagemSchema.MensagemSchema import (
    MensagemAtualizarResponse,
    MensagemPorIdResponse,
    MensagemAtualizar
)

router = APIRouter(
    prefix="/mensagem",
    tags=["Mensagem"]
)

@router.post('/criar-mensagem')
def criar_mensagem(mensagem: MensagemChatCreate, db: Session = Depends(get_db)):
    nova_mensagem = MensagemChatDB(
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

@router.get('/{id_mensagem}', response_model=MensagemPorIdResponse)
def obter_mensagem(id_mensagem: int, db: Session = Depends(get_db)):
    mensagem_banco = db.query(MensagemChatDB).filter(MensagemChatDB.id_mensagem == id_mensagem).first()

    if not mensagem_banco:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return  mensagem_banco

@router.patch('/{id_mensagem}', response_model=MensagemAtualizarResponse)
def atualizar_mensagem(
        id_mensagem: int, 
        mensagem_data: MensagemAtualizar,
        db: Session = Depends(get_db) 
        ):
    mensagem_banco = db.query(MensagemChatDB).filter(MensagemChatDB.id_mensagem == id_mensagem).first()

    if not mensagem_banco:
        raise HTTPException(status_code=404, detail=("Mensagem não encontrada"))

    mensagem_atualizada = mensagem_banco.model_dump(exclude_unset=True)

    for chave, valor in mensagem_atualizada.items():
        setattr(mensagem_banco, chave, valor)

    db.commit()
    db.refresh(mensagem_banco)

    return mensagem_banco

@router.delete('/{id_mensagem}')
def deletar_mensagem(id_mensagem: int, db: Session = Depends(get_db)):
    mensagem_banco = db.query(MensagemChatDB).filter(MensagemChatDB.id_mensagem == id_mensagem). first()

    if not mensagem_banco:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")

    db.delete(mensagem_banco)
    db.commit()

    return "Mensagem deletada com sucesso"