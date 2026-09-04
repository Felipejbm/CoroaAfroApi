"""Chat privado por vínculo. Sem leitura ou migração de mensagens legadas sem autoria."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from database import get_db
from models import (
    MentoriaDB, 
    MentorAccessDB, 
    MentorDB, 
    EmpreendedorDB,
    MentorSessionDB, 
    MentoriaMensagemDB as Mensagem
    )
from security import (
    COOKIE_NAME, 
    token_hash, 
    )
from dependencies import (
    get_auth_session,
    get_current_mentor,
    get_current_user
)


def sem_cache(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/mentoria', tags=['Chat de mentoria'], dependencies=[Depends(sem_cache)])


def participante(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get(COOKIE_NAME, '')
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        mentor = get_current_mentor(request, db)
        return ('mentor', mentor.id_mentor)
    user = get_current_user(get_auth_session(request, db), db)
    return ('empreendedor', user.id_empreendedor)


def vinculo_autorizado(db, ator, mentor_id, empreendedor_id, lock=False):
    papel, identidade = ator
    if identidade != (mentor_id if papel == 'mentor' else empreendedor_id):
        raise HTTPException(404, 'Conversa não disponível para esta conta.')
    acesso_query = db.query(MentorAccessDB).filter_by(id_mentor=mentor_id)
    acesso = (acesso_query.with_for_update() if lock else acesso_query).first()
    query = db.query(MentoriaDB).filter_by(id_mentor=mentor_id, id_empreendedor=empreendedor_id)
    vinculo = (query.with_for_update() if lock else query).first()
    if not acesso or not acesso.ativo or not vinculo or not vinculo.ativo:
        raise HTTPException(404, 'Conversa não disponível. O vínculo precisa estar ativo.')
    return vinculo


def mensagens_da_dupla(db, mentor_id, empreendedor_id):
    return db.query(Mensagem).filter_by(id_mentor=mentor_id, id_empreendedor=empreendedor_id)


def saida(mensagem, ator):
    return {'id': mensagem.id, 'texto': mensagem.texto, 'remetente': mensagem.remetente,
            'minha': mensagem.remetente == ator[0],
            'criado_em': mensagem.criado_em.replace(tzinfo=timezone.utc).isoformat()}


@router.get('/chat/conversas')
def conversas(ator=Depends(participante), db: Session = Depends(get_db)):
    papel, identidade = ator
    query = db.query(MentoriaDB).join(MentorAccessDB, MentorAccessDB.id_mentor == MentoriaDB.id_mentor).filter(
        MentoriaDB.ativo.is_(True), MentorAccessDB.ativo.is_(True))
    query = query.filter(MentoriaDB.id_mentor == identidade if papel == 'mentor'
                         else MentoriaDB.id_empreendedor == identidade)
    resultado = []
    for vinculo in query.order_by(MentoriaDB.id_mentor, MentoriaDB.id_empreendedor).all():
        pessoa = db.get(EmpreendedorDB, vinculo.id_empreendedor) if papel == 'mentor' else db.get(MentorDB, vinculo.id_mentor)
        ultima = mensagens_da_dupla(db, vinculo.id_mentor, vinculo.id_empreendedor).order_by(Mensagem.id.desc()).first()
        resultado.append({'id_mentor': vinculo.id_mentor, 'id_empreendedor': vinculo.id_empreendedor,
                          'nome': pessoa.nome, 'papel': 'empreendedor' if papel == 'mentor' else 'mentor',
                          'ultima_mensagem': saida(ultima, ator) if ultima else None})
    return sorted(resultado, key=lambda c: c['ultima_mensagem']['id'] if c['ultima_mensagem'] else 0, reverse=True)


@router.get('/chat/conversas/{mentor_id}/{empreendedor_id}/mensagens')
def listar(mentor_id: int, empreendedor_id: int, antes: int | None = Query(default=None, ge=1),
           depois: int | None = Query(default=None, ge=0), ator=Depends(participante), db: Session = Depends(get_db)):
    vinculo_autorizado(db, ator, mentor_id, empreendedor_id)
    if antes is not None and depois is not None:
        raise HTTPException(422, 'Use apenas um cursor por consulta.')
    query = mensagens_da_dupla(db, mentor_id, empreendedor_id)
    if depois is not None:
        rows = query.filter(Mensagem.id > depois).order_by(Mensagem.id).limit(51).all()
        itens = rows[:50]
    else:
        if antes is not None:
            query = query.filter(Mensagem.id < antes)
        rows = query.order_by(Mensagem.id.desc()).limit(51).all()
        itens = list(reversed(rows[:50]))
    return {'mensagens': [saida(m, ator) for m in itens], 'tem_mais': len(rows) > 50}


class Envio(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    texto: str = Field(min_length=1, max_length=4000)
    chave_envio: UUID


@router.post('/chat/conversas/{mentor_id}/{empreendedor_id}/mensagens')
def enviar(mentor_id: int, empreendedor_id: int, entrada: Envio,
           ator=Depends(participante), db: Session = Depends(get_db)):
    vinculo_autorizado(db, ator, mentor_id, empreendedor_id, lock=True)
    chave = str(entrada.chave_envio)
    existente = mensagens_da_dupla(db, mentor_id, empreendedor_id).filter_by(remetente=ator[0], chave_envio=chave).first()
    if existente:
        if existente.texto != entrada.texto:
            raise HTTPException(409, 'Esta tentativa de envio já foi usada para outra mensagem.')
        return saida(existente, ator)
    mensagem = Mensagem(id_mentor=mentor_id, id_empreendedor=empreendedor_id, remetente=ator[0],
                        texto=entrada.texto, chave_envio=chave,
                        criado_em=datetime.now(timezone.utc).replace(tzinfo=None))
    db.add(mensagem)
    db.commit()
    return saida(mensagem, ator)
