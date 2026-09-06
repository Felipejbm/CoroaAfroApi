from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import EmpreendedorDB, IaConversaDB, IaMensagemDB
from schemas.IaSchema.IaSchema import (
    IaConversaCriar,
    IaConversaPublica,
    IaMensagemCriar,
    IaMensagemPublica,
    IaResposta,
)
from services.ia_service import IaService, IaServiceError, get_ia_service
from services.ia_contexto import montar_contexto_ia
from services.ia_modos import listar_modos_ia


router = APIRouter(prefix="/ia", tags=["Assistente IA"])


@router.get("/modos")
def listar_modos():
    """Opções que o front pode exibir como atalhos da assistente."""
    return listar_modos_ia()


def obter_conversa_do_usuario(
    id_conversa: int,
    usuario: EmpreendedorDB,
    db: Session,
) -> IaConversaDB:
    conversa = db.query(IaConversaDB).filter(
        IaConversaDB.id_conversa == id_conversa,
        IaConversaDB.id_empreendedor == usuario.id_empreendedor,
    ).first()
    if not conversa:
        raise HTTPException(404, "Conversa não encontrada.")
    return conversa


@router.post("/conversas", response_model=IaConversaPublica, status_code=201)
def criar_conversa(
    dados: IaConversaCriar,
    db: Session = Depends(get_db),
    usuario: EmpreendedorDB = Depends(get_current_user),
):
    conversa = IaConversaDB(
        id_empreendedor=usuario.id_empreendedor,
        titulo=dados.titulo,
    )
    db.add(conversa)
    db.commit()
    db.refresh(conversa)
    return conversa


@router.get("/conversas", response_model=list[IaConversaPublica])
def listar_conversas(
    incluir_arquivadas: bool = False,
    db: Session = Depends(get_db),
    usuario: EmpreendedorDB = Depends(get_current_user),
):
    consulta = db.query(IaConversaDB).filter(
        IaConversaDB.id_empreendedor == usuario.id_empreendedor
    )
    if not incluir_arquivadas:
        consulta = consulta.filter(IaConversaDB.arquivada.is_(False))
    return consulta.order_by(IaConversaDB.atualizada_em.desc()).all()


@router.get("/conversas/{id_conversa}/mensagens", response_model=list[IaMensagemPublica])
def listar_mensagens(
    id_conversa: int,
    limite: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: EmpreendedorDB = Depends(get_current_user),
):
    obter_conversa_do_usuario(id_conversa, usuario, db)
    return db.query(IaMensagemDB).filter(
        IaMensagemDB.id_conversa == id_conversa
    ).order_by(IaMensagemDB.id_mensagem.asc()).limit(limite).all()


@router.post("/conversas/{id_conversa}/mensagens", response_model=IaResposta)
async def enviar_mensagem(
    id_conversa: int,
    dados: IaMensagemCriar,
    db: Session = Depends(get_db),
    usuario: EmpreendedorDB = Depends(get_current_user),
    ia_service: IaService = Depends(get_ia_service),
):
    conversa = obter_conversa_do_usuario(id_conversa, usuario, db)
    if conversa.arquivada:
        raise HTTPException(409, "Reabra a conversa antes de enviar uma mensagem.")

    mensagens_anteriores = db.query(IaMensagemDB).filter(
        IaMensagemDB.id_conversa == conversa.id_conversa
    ).order_by(IaMensagemDB.id_mensagem.desc()).limit(12).all()
    historico = [
        {
            "role": "user" if mensagem.papel == "usuario" else "assistant",
            "content": mensagem.conteudo,
        }
        for mensagem in reversed(mensagens_anteriores)
    ]

    try:
        resultado = await ia_service.gerar_resposta(
            id_empreendedor=usuario.id_empreendedor,
            contexto=await montar_contexto_ia(usuario, db),
            historico=historico,
            pergunta=dados.conteudo,
            modo=dados.modo,
        )
    except IaServiceError as exc:
        raise HTTPException(exc.status_code, exc.mensagem) from exc

    mensagem_usuario = IaMensagemDB(
        id_conversa=conversa.id_conversa,
        papel="usuario",
        conteudo=dados.conteudo,
    )
    mensagem_assistente = IaMensagemDB(
        id_conversa=conversa.id_conversa,
        papel="assistente",
        conteudo=resultado.texto,
        tokens_entrada=resultado.tokens_entrada,
        tokens_saida=resultado.tokens_saida,
    )
    conversa.atualizada_em = datetime.now()
    db.add_all([mensagem_usuario, mensagem_assistente])
    db.commit()
    db.refresh(conversa)
    db.refresh(mensagem_usuario)
    db.refresh(mensagem_assistente)
    return IaResposta(
        conversa=conversa,
        mensagem_usuario=mensagem_usuario,
        mensagem_assistente=mensagem_assistente,
    )


@router.patch("/conversas/{id_conversa}/arquivar", status_code=204)
def arquivar_conversa(
    id_conversa: int,
    db: Session = Depends(get_db),
    usuario: EmpreendedorDB = Depends(get_current_user),
):
    conversa = obter_conversa_do_usuario(id_conversa, usuario, db)
    conversa.arquivada = True
    conversa.atualizada_em = datetime.now()
    db.commit()
    return Response(status_code=204)
