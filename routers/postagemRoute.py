from datetime import datetime, timezone
from hashlib import sha256
from fastapi import APIRouter, Depends, HTTPException, Response, Request, UploadFile, File, Form
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_auth_session, get_current_user, get_current_mentor
from security import COOKIE_NAME, token_hash
from models import EmpreendedorDB, MentorDB, MentorSessionDB, PostagemChatDB, PostagemComentarioDB
from services.foto_perfil import LIMITE_FOTO, normalizar_foto
from schemas.PostagemSchema.PostagemSchema import (
    PostagemPorIdResponse, PostagemAtualizar, PostagemChatCreate,
    ComentarioCreate, ComentarioResponse,
)


def participante(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get(COOKIE_NAME, '')
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        pessoa = get_current_mentor(request, db)
        return ('mentor', pessoa.id_mentor)
    pessoa = get_current_user(get_auth_session(request, db), db)
    return ('empreendedor', pessoa.id_empreendedor)


def sem_cache(response: Response):
    response.headers['Cache-Control'] = 'no-store'

router = APIRouter(prefix='/postagem', tags=['Postagem'],
                   dependencies=[Depends(participante), Depends(sem_cache)])


def identidade(post):
    return ('mentor', post.id_mentor) if post.id_mentor is not None else ('empreendedor', post.fk_empreendedor_id_empreendedor)


def buscar(db, id_post):
    post = db.get(PostagemChatDB, id_post)
    if not post or (post.fk_empreendedor_id_empreendedor is None and post.id_mentor is None):
        raise HTTPException(404, 'Postagem não encontrada.')
    return post


def autorizar(post, ator):
    if identidade(post) != ator:
        raise HTTPException(403, 'Somente o autor pode alterar esta postagem.')


def comentario_saida(db, comentario):
    mentor = comentario.id_mentor is not None
    autor = db.get(MentorDB if mentor else EmpreendedorDB, comentario.id_mentor if mentor else comentario.id_empreendedor)
    return dict(id=comentario.id, author=autor.nome if autor else 'Autor indisponível', text=comentario.texto,
                autorId=comentario.id_mentor if mentor else comentario.id_empreendedor,
                autorPapel='mentor' if mentor else 'empreendedor')


def saida(db, post, ator):
    papel, autor_id = identidade(post)
    autor = db.get(MentorDB if papel == 'mentor' else EmpreendedorDB, autor_id)
    foto = getattr(autor, 'foto_perfil', None)
    comentarios = db.query(PostagemComentarioDB).filter_by(id_post=post.id_post).order_by(PostagemComentarioDB.id).all()
    return dict(id_post=post.id_post, conteudo_texto=post.conteudo_texto,
                midia_url=post.midia_url, data_publicacao=post.data_publicacao,
                autor_id=autor_id, autor_papel=papel, minha=autor is not None and identidade(post) == ator,
                autor_foto_url=f'/postagem/{post.id_post}/autor/foto?v={sha256(foto).hexdigest()[:16]}' if foto else None,
                imagem_upload_url=f'/postagem/{post.id_post}/imagem?v={post.imagem_hash}' if post.imagem_hash else None,
                company=autor.nome if autor else 'Autor indisponível', segment='Mentor' if papel == 'mentor' else 'Empreendedor',
                comments=[comentario_saida(db, c) for c in comentarios])


def novo_post(entrada, ator):
    return PostagemChatDB(**entrada.model_dump(),
        fk_empreendedor_id_empreendedor=ator[1] if ator[0] == 'empreendedor' else None,
        id_mentor=ator[1] if ator[0] == 'mentor' else None,
        data_publicacao=datetime.now(timezone.utc).date())


def salvar(db, post, ator):
    db.add(post)
    db.commit()
    db.refresh(post)
    return saida(db, post, ator)


def formulario(conteudo_texto, midia_url):
    try:
        return PostagemChatCreate(conteudo_texto=conteudo_texto, midia_url=midia_url)
    except ValidationError:
        raise HTTPException(422, 'Confira o texto (até 4.000 caracteres) e a URL da imagem (até 255 caracteres).')


def ler_imagem(imagem):
    try:
        return normalizar_foto(imagem.file.read(LIMITE_FOTO + 1), imagem.content_type, tamanho=1920)
    finally:
        imagem.file.close()


def definir_imagem(post, dados):
    post.imagem = dados
    post.imagem_hash = sha256(dados).hexdigest() if dados else None
    post.midia_url = None


@router.post('/criar-postagem', response_model=PostagemPorIdResponse, status_code=201)
def criar_postagem(postagem: PostagemChatCreate, db: Session = Depends(get_db), ator=Depends(participante)):
    return salvar(db, novo_post(postagem, ator), ator)


@router.post('/criar-com-imagem', response_model=PostagemPorIdResponse, status_code=201)
def criar_com_imagem(conteudo_texto: str = Form(...), imagem: UploadFile = File(...),
                     db: Session = Depends(get_db), ator=Depends(participante)):
    post = novo_post(formulario(conteudo_texto, None), ator)
    definir_imagem(post, ler_imagem(imagem))
    return salvar(db, post, ator)


@router.get('', response_model=list[PostagemPorIdResponse])
def listar_postagens(db: Session = Depends(get_db), ator=Depends(participante)):
    posts = db.query(PostagemChatDB).filter(or_(
        PostagemChatDB.fk_empreendedor_id_empreendedor.isnot(None), PostagemChatDB.id_mentor.isnot(None)
    )).order_by(PostagemChatDB.id_post.desc()).all()
    return [saida(db, post, ator) for post in posts]


@router.get('/{id_post}/imagem')
def obter_imagem(id_post: int, db: Session = Depends(get_db)):
    post = buscar(db, id_post)
    if not post.imagem_hash:
        raise HTTPException(404, 'Imagem não encontrada.')
    return Response(post.imagem, media_type='image/jpeg', headers={
        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/{id_post}/autor/foto')
def obter_foto_autor(id_post: int, db: Session = Depends(get_db)):
    papel, autor_id = identidade(buscar(db, id_post))
    autor = db.get(MentorDB if papel == 'mentor' else EmpreendedorDB, autor_id)
    foto = getattr(autor, 'foto_perfil', None)
    if not foto:
        raise HTTPException(404, 'O autor não possui foto de perfil.')
    return Response(foto, media_type='image/jpeg', headers={
        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/{id_post}', response_model=PostagemPorIdResponse)
def obter_postagem_por_id(id_post: int, db: Session = Depends(get_db), ator=Depends(participante)):
    return saida(db, buscar(db, id_post), ator)


@router.patch('/{id_post}', response_model=PostagemPorIdResponse)
def atualizar_postagem(id_post: int, postagem_data: PostagemAtualizar,
                       db: Session = Depends(get_db), ator=Depends(participante)):
    post = buscar(db, id_post)
    autorizar(post, ator)
    if 'midia_url' in postagem_data.model_fields_set:
        definir_imagem(post, None)
    for chave, valor in postagem_data.model_dump(exclude_unset=True).items():
        setattr(post, chave, valor)
    return salvar(db, post, ator)


@router.patch('/{id_post}/com-imagem', response_model=PostagemPorIdResponse)
def editar_com_imagem(id_post: int, conteudo_texto: str = Form(...), imagem: UploadFile = File(...),
                      db: Session = Depends(get_db), ator=Depends(participante)):
    post = buscar(db, id_post)
    autorizar(post, ator)
    entrada = formulario(conteudo_texto, None)
    dados = ler_imagem(imagem)
    post.conteudo_texto = entrada.conteudo_texto
    definir_imagem(post, dados)
    return salvar(db, post, ator)


@router.delete('/{id_post}', status_code=204)
def deletar_postagem(id_post: int, db: Session = Depends(get_db), ator=Depends(participante)):
    post = buscar(db, id_post)
    autorizar(post, ator)
    db.query(PostagemComentarioDB).filter_by(id_post=id_post).delete()
    db.delete(post)
    db.commit()


@router.post('/{id_post}/comentarios', response_model=ComentarioResponse, status_code=201)
def comentar(id_post: int, entrada: ComentarioCreate, db: Session = Depends(get_db), ator=Depends(participante)):
    buscar(db, id_post)
    comentario = PostagemComentarioDB(id_post=id_post,
        id_empreendedor=ator[1] if ator[0] == 'empreendedor' else None,
        id_mentor=ator[1] if ator[0] == 'mentor' else None, texto=entrada.texto)
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario_saida(db, comentario)
