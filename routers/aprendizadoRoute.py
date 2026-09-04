"""Trilhas autorais: conteúdo publicado é imutável para preservar o progresso."""
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy import or_
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from database import get_db
from models import (
    MentorDB, 
    MentorAccessDB, 
    EmpreendedorDB,
    MentoriaDB,
    MentoriaTrilhaDB as Trilha, 
    MentoriaAulaDB as Aula,
    MentoriaAtribuicaoDB as Atribuicao, 
    MentoriaProgressoDB as Progresso,
    MentoriaCatalogoDB as Catalogo
    )
from dependencies import get_current_mentor, get_current_user


def no_cache(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/mentoria", tags=["Aprendizado"], dependencies=[Depends(no_cache)])


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AulaEntrada(Entrada):
    titulo: str = Field(min_length=1, max_length=150)
    conteudo: str = Field(min_length=1, max_length=15000)
    video_url: str = Field(default="", max_length=2048)

    @field_validator("video_url")
    @classmethod
    def video_seguro(cls, value):
        if not value:
            return value
        url = urlsplit(value)
        if (url.scheme != "https" or url.hostname not in
                {"youtube.com", "www.youtube.com", "youtu.be", "vimeo.com", "www.vimeo.com"}
                or url.username or url.password or url.port not in (None, 443)):
            raise ValueError("Use um link HTTPS do YouTube ou Vimeo.")
        return value


class TrilhaEntrada(Entrada):
    titulo: str = Field(min_length=1, max_length=150)
    descricao: str = Field(default="", max_length=3000)
    aulas: list[AulaEntrada] = Field(default_factory=list, max_length=30)
    categoria: str = "geral"
    publico_alvo: str = Field(default="", max_length=500)

    @field_validator("categoria")
    @classmethod
    def categoria_valida(cls, value):
        if value not in CATEGORIAS:
            raise ValueError("Escolha uma categoria disponível.")
        return value


CATEGORIAS = {
    "instagram": "Instagram", "marketing_digital": "Marketing digital",
    "marketing_local": "Marketing local e presencial", "vendas": "Vendas",
    "gestao": "Gestão do negócio", "financas": "Finanças",
    "marca": "Marca e identidade visual", "geral": "Geral",
}


def opcoes():
    return [{"value": key, "label": value} for key, value in CATEGORIAS.items()]


@router.get("/trilhas/categorias")
def categorias_mentor(mentor: MentorDB = Depends(get_current_mentor)):
    return opcoes()


@router.get("/catalogo/categorias")
def categorias_empreendedor(user: EmpreendedorDB = Depends(get_current_user)):
    return opcoes()


def metadados(db, trilha):
    item = db.get(Catalogo, trilha.id)
    categoria = item.categoria if item else "geral"
    mentor = db.get(MentorDB, trilha.id_mentor)
    return {"categoria": categoria, "categoria_label": CATEGORIAS.get(categoria, "Geral"),
            "publico_alvo": item.publico_alvo if item else "",
            "mentor": {"id": mentor.id_mentor, "nome": mentor.nome, "especialidade": mentor.especialidade}}


def salvar_metadados(db, trilha, entrada):
    item = db.get(Catalogo, trilha.id)
    if not item:
        item = Catalogo(id_trilha=trilha.id)
        db.add(item)
    item.categoria, item.publico_alvo = entrada.categoria, entrada.publico_alvo


class TrilhaEdicao(TrilhaEntrada):
    versao: int = Field(ge=1)


class VersaoEntrada(Entrada):
    versao: int = Field(ge=1)


class ApresentacaoEntrada(VersaoEntrada):
    categoria: str
    publico_alvo: str = Field(default="", max_length=500)

    @field_validator("categoria")
    @classmethod
    def categoria_valida(cls, value):
        if value not in CATEGORIAS:
            raise ValueError("Escolha uma categoria disponível.")
        return value


@router.patch("/trilhas/{trilha_id}/catalogo")
def atualizar_apresentacao(trilha_id: int, entrada: ApresentacaoEntrada,
                           mentor: MentorDB = Depends(get_current_mentor), db: Session = Depends(get_db)):
    trilha = propria(db, mentor, trilha_id, lock=True)
    if trilha.versao != entrada.versao:
        raise HTTPException(409, "A trilha foi alterada. Recarregue antes de salvar.")
    salvar_metadados(db, trilha, entrada)
    trilha.versao += 1
    db.commit()
    return saida(db, trilha)


class ProgressoEntrada(Entrada):
    concluida: bool = Field(strict=True)


def propria(db, mentor, trilha_id, lock=False):
    query = db.query(Trilha).filter(Trilha.id == trilha_id, Trilha.id_mentor == mentor.id_mentor)
    trilha = (query.with_for_update() if lock else query).first()
    if not trilha:
        raise HTTPException(404, "Trilha não encontrada.")
    return trilha


def aulas_da_trilha(db, trilha_id):
    return db.query(Aula).filter(Aula.id_trilha == trilha_id).order_by(Aula.ordem, Aula.id).all()


def saida(db, trilha, empreendedor_id=None):
    aulas = aulas_da_trilha(db, trilha.id)
    concluidas = set()
    if empreendedor_id is not None:
        concluidas = {p.id_aula for p in db.query(Progresso).join(Aula, Aula.id == Progresso.id_aula)
                      .filter(Aula.id_trilha == trilha.id, Progresso.id_empreendedor == empreendedor_id,
                              Progresso.concluida.is_(True)).all()}
    return {"id": trilha.id, "titulo": trilha.titulo, "descricao": trilha.descricao, **metadados(db, trilha),
            "publicada": trilha.publicada, "versao": trilha.versao,
            "progresso": round(100 * len(concluidas) / len(aulas)) if aulas else 0,
            "aulas": [{"id": a.id, "titulo": a.titulo, "conteudo": a.conteudo,
                       "video_url": a.video_url or "", "concluida": a.id in concluidas} for a in aulas]}


def adicionar_aulas(db, trilha, entradas):
    for ordem, entrada in enumerate(entradas):
        db.add(Aula(id_trilha=trilha.id, ordem=ordem, **entrada.model_dump()))


@router.get("/trilhas")
def listar(mentor: MentorDB = Depends(get_current_mentor), db: Session = Depends(get_db)):
    return [saida(db, t) for t in db.query(Trilha).filter(Trilha.id_mentor == mentor.id_mentor)
            .order_by(Trilha.id.desc()).all()]


@router.post("/trilhas", status_code=201)
def criar(entrada: TrilhaEntrada, mentor: MentorDB = Depends(get_current_mentor), db: Session = Depends(get_db)):
    trilha = Trilha(id_mentor=mentor.id_mentor, titulo=entrada.titulo, descricao=entrada.descricao)
    db.add(trilha)
    db.flush()
    adicionar_aulas(db, trilha, entrada.aulas)
    salvar_metadados(db, trilha, entrada)
    db.commit()
    return saida(db, trilha)


@router.put("/trilhas/{trilha_id}")
def editar(trilha_id: int, entrada: TrilhaEdicao, mentor: MentorDB = Depends(get_current_mentor),
           db: Session = Depends(get_db)):
    trilha = propria(db, mentor, trilha_id, lock=True)
    if trilha.publicada or trilha.versao != entrada.versao:
        raise HTTPException(409, "Trilha publicada ou alterada em outra aba. Recarregue a lista.")
    trilha.titulo, trilha.descricao = entrada.titulo, entrada.descricao
    salvar_metadados(db, trilha, entrada)
    trilha.versao += 1
    db.query(Aula).filter(Aula.id_trilha == trilha.id).delete(synchronize_session=False)
    adicionar_aulas(db, trilha, entrada.aulas)
    db.commit()
    return saida(db, trilha)


@router.post("/trilhas/{trilha_id}/publicar")
def publicar(trilha_id: int, entrada: VersaoEntrada, mentor: MentorDB = Depends(get_current_mentor),
             db: Session = Depends(get_db)):
    trilha = propria(db, mentor, trilha_id, lock=True)
    if trilha.versao != entrada.versao:
        raise HTTPException(409, "A trilha foi alterada. Recarregue antes de publicar.")
    if not aulas_da_trilha(db, trilha.id):
        raise HTTPException(422, "Adicione pelo menos uma aula antes de publicar.")
    if not trilha.publicada:
        trilha.publicada = True
        trilha.versao += 1
    db.commit()
    return saida(db, trilha)


@router.put("/trilhas/{trilha_id}/mentorados/{empreendedor_id}")
def atribuir(trilha_id: int, empreendedor_id: int, mentor: MentorDB = Depends(get_current_mentor),
             db: Session = Depends(get_db)):
    raise HTTPException(403, "A inscrição deve ser feita pelo próprio empreendedor no catálogo.")


@router.get("/catalogo")
def catalogo(categoria: str = Query(default="", max_length=32), pagina: int = Query(default=1, ge=1),
             user: EmpreendedorDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if categoria and categoria not in CATEGORIAS:
        raise HTTPException(422, "Categoria inválida.")
    bloqueio = db.query(MentoriaDB.id_mentor).filter(
        MentoriaDB.id_mentor == Trilha.id_mentor, MentoriaDB.id_empreendedor == user.id_empreendedor,
        MentoriaDB.ativo.is_(False)).exists()
    query = db.query(Trilha).join(MentorAccessDB, MentorAccessDB.id_mentor == Trilha.id_mentor).filter(
        Trilha.publicada.is_(True), MentorAccessDB.ativo.is_(True), ~bloqueio)
    if categoria:
        query = query.outerjoin(Catalogo, Catalogo.id_trilha == Trilha.id)
        query = query.filter(or_(Catalogo.categoria == "geral", Catalogo.id_trilha.is_(None))
                             if categoria == "geral" else Catalogo.categoria == categoria)
    total = query.count()
    itens = []
    for trilha in query.order_by(Trilha.id.desc()).offset((pagina - 1) * 12).limit(12).all():
        aulas = db.query(Aula.id, Aula.titulo).filter(Aula.id_trilha == trilha.id).order_by(Aula.ordem).all()
        itens.append({"id": trilha.id, "titulo": trilha.titulo, "descricao": trilha.descricao,
                      **metadados(db, trilha), "aulas": [{"titulo": a.titulo} for a in aulas],
                      "inscrito": db.get(Atribuicao, (trilha.id, user.id_empreendedor)) is not None})
    return {"itens": itens, "total": total, "pagina": pagina, "por_pagina": 12}


@router.post("/catalogo/{trilha_id}/inscricao")
def inscrever(trilha_id: int, user: EmpreendedorDB = Depends(get_current_user), db: Session = Depends(get_db)):
    # Serializa inscrições da mesma pessoa, inclusive em trilhas distintas do mesmo mentor.
    db.query(EmpreendedorDB).filter(EmpreendedorDB.id_empreendedor == user.id_empreendedor).with_for_update().one()
    trilha = db.query(Trilha).filter(Trilha.id == trilha_id, Trilha.publicada.is_(True)).first()
    if not trilha:
        raise HTTPException(404, "Trilha não disponível.")
    acesso = db.query(MentorAccessDB).filter(MentorAccessDB.id_mentor == trilha.id_mentor).with_for_update().first()
    if not acesso or not acesso.ativo:
        raise HTTPException(404, "Trilha não disponível.")
    vinculo = db.query(MentoriaDB).filter_by(id_mentor=trilha.id_mentor,
                 id_empreendedor=user.id_empreendedor).with_for_update().first()
    if vinculo and not vinculo.ativo:
        raise HTTPException(403, "Este vínculo foi desativado pela equipe. Entre em contato para revisão.")
    if not vinculo:
        db.add(MentoriaDB(id_mentor=trilha.id_mentor, id_empreendedor=user.id_empreendedor, ativo=True))
    if not db.get(Atribuicao, (trilha.id, user.id_empreendedor)):
        db.add(Atribuicao(id_trilha=trilha.id, id_empreendedor=user.id_empreendedor))
        for aula in aulas_da_trilha(db, trilha.id):
            db.add(Progresso(id_aula=aula.id, id_empreendedor=user.id_empreendedor))
    db.commit()
    return saida(db, trilha, user.id_empreendedor)


def disponiveis(db, empreendedor_id):
    # Revogar o mentor ou o vínculo também revoga leitura e atualização das aulas.
    return db.query(Trilha).join(Atribuicao, Atribuicao.id_trilha == Trilha.id).join(
        MentoriaDB, (MentoriaDB.id_mentor == Trilha.id_mentor) &
        (MentoriaDB.id_empreendedor == Atribuicao.id_empreendedor)).join(
        MentorAccessDB, MentorAccessDB.id_mentor == Trilha.id_mentor).filter(
        Atribuicao.id_empreendedor == empreendedor_id, Trilha.publicada.is_(True),
        MentoriaDB.ativo.is_(True), MentorAccessDB.ativo.is_(True))


@router.get("/minhas-trilhas")
def minhas(user: EmpreendedorDB = Depends(get_current_user), db: Session = Depends(get_db)):
    return [saida(db, t, user.id_empreendedor) for t in disponiveis(db, user.id_empreendedor)
            .order_by(Trilha.id.desc()).all()]


@router.get("/mentorados/{empreendedor_id}/trilhas")
def acompanhamento(empreendedor_id: int, mentor: MentorDB = Depends(get_current_mentor),
                   db: Session = Depends(get_db)):
    vinculo = db.get(MentoriaDB, (mentor.id_mentor, empreendedor_id))
    if not vinculo or not vinculo.ativo:
        raise HTTPException(404, "Mentorado não encontrado para este mentor.")
    return [saida(db, t, empreendedor_id) for t in disponiveis(db, empreendedor_id)
            .filter(Trilha.id_mentor == mentor.id_mentor).order_by(Trilha.id.desc()).all()]


@router.put("/minhas-trilhas/{trilha_id}/aulas/{aula_id}")
def concluir(trilha_id: int, aula_id: int, entrada: ProgressoEntrada,
             user: EmpreendedorDB = Depends(get_current_user), db: Session = Depends(get_db)):
    trilha = disponiveis(db, user.id_empreendedor).filter(Trilha.id == trilha_id).first()
    aula = db.get(Aula, aula_id)
    if not trilha or not aula or aula.id_trilha != trilha.id:
        raise HTTPException(404, "Aula não encontrada para esta conta.")
    progresso = db.get(Progresso, (aula_id, user.id_empreendedor))
    if not progresso:
        raise HTTPException(404, "Aula não atribuída.")
    progresso.concluida = entrada.concluida
    db.commit()
    return saida(db, trilha, user.id_empreendedor)
