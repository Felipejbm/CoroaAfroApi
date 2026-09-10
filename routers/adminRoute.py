import hmac, secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from config import get_settings
from database import get_db
from models import AdminSessionDB, EmpreendedorDB, FeedbackDB, MentorAccessDB, MentorDB, MentorSolicitacaoDB, MentoriaAvaliacaoDB, MentoriaTrilhaDB
from security import token_hash, validate_origin

router = APIRouter(prefix="/admin", tags=["Administração"])
ADMIN_COOKIE = "coroa_admin_session"

class LoginAdmin(BaseModel):
    email: str
    senha: str
class Analise(BaseModel):
    motivo: str | None = Field(default=None, max_length=500)

def admin_atual(request: Request, db: Session = Depends(get_db)):
    raw = request.cookies.get(ADMIN_COOKIE, "")
    sessao = db.get(AdminSessionDB, token_hash(raw)) if raw else None
    if not sessao or sessao.expires_at <= datetime.utcnow():
        raise HTTPException(401, "Entre como administrador.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}: validate_origin(request)
    return sessao

def serializar(item):
    return {"id": item.id, "nome": item.nome, "email": item.email, "especialidade": item.especialidade, "biografia": item.biografia, "status": item.status, "motivo_recusa": item.motivo_recusa, "criada_em": item.criada_em, "analisada_em": item.analisada_em}

def serializar_feedback(item):
    return {"id": item.id_feedback, "autor_nome": item.autor_nome, "autor_papel": item.autor_papel,
            "nota": item.nota, "comentario": item.comentario,
            "autoriza_publicacao": item.autoriza_publicacao, "status": item.status,
            "criado_em": item.criado_em, "analisado_em": item.analisado_em}

@router.post("/login", dependencies=[Depends(validate_origin)])
def login(dados: LoginAdmin, response: Response, db: Session = Depends(get_db)):
    cfg = get_settings(); senha = cfg.admin_password.get_secret_value() if cfg.admin_password else ""
    email_ok = bool(cfg.admin_email) and hmac.compare_digest(dados.email.strip().lower(), cfg.admin_email.strip().lower())
    if not email_ok or not senha or not hmac.compare_digest(dados.senha, senha):
        raise HTTPException(401, "Credenciais administrativas inválidas.")
    token = secrets.token_urlsafe(32)
    db.add(AdminSessionDB(token_hash=token_hash(token), expires_at=datetime.utcnow()+timedelta(hours=4))); db.commit()
    response.set_cookie(ADMIN_COOKIE, token, max_age=14400, httponly=True, samesite=cfg.session_cookie_samesite, secure=cfg.session_cookie_secure, path="/")
    return {"message": "Acesso administrativo confirmado."}

@router.get("/me")
def me(_: AdminSessionDB = Depends(admin_atual)): return {"papel": "admin"}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    raw=request.cookies.get(ADMIN_COOKIE, ""); db.query(AdminSessionDB).filter_by(token_hash=token_hash(raw)).delete(); db.commit(); response.delete_cookie(ADMIN_COOKIE, path="/"); return {"message":"Sessão encerrada."}

@router.get("/mentor-solicitacoes")
def listar(status: str | None = None, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    query=db.query(MentorSolicitacaoDB)
    if status: query=query.filter_by(status=status)
    return [serializar(x) for x in query.order_by(MentorSolicitacaoDB.id.desc()).all()]

@router.post("/mentor-solicitacoes/{solicitacao_id}/aprovar")
def aprovar(solicitacao_id: int, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    item=db.get(MentorSolicitacaoDB, solicitacao_id)
    if not item or item.status != "pendente": raise HTTPException(409, "Solicitação indisponível para aprovação.")
    if db.query(MentorAccessDB).filter_by(email=item.email).first():
        raise HTTPException(409, "Já existe um mentor autorizado com este e-mail.")
    try:
        mentor=MentorDB(nome=item.nome, especialidade=item.especialidade, biografia=item.biografia); db.add(mentor); db.flush()
        db.add(MentorAccessDB(id_mentor=mentor.id_mentor, email=item.email, senha_hash=item.senha_hash, ativo=True)); item.status="aprovada"; item.analisada_em=datetime.utcnow(); db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Não foi possível aprovar porque estes dados já pertencem a outro mentor.")
    return serializar(item)

@router.post("/mentor-solicitacoes/{solicitacao_id}/recusar")
def recusar(solicitacao_id: int, dados: Analise, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    item=db.get(MentorSolicitacaoDB, solicitacao_id)
    if not item or item.status != "pendente": raise HTTPException(409, "Solicitação indisponível para recusa.")
    item.status="recusada"; item.motivo_recusa=dados.motivo; item.analisada_em=datetime.utcnow(); db.commit(); return serializar(item)

@router.get("/feedbacks")
def listar_feedbacks(status: str | None = None, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    query = db.query(FeedbackDB)
    if status: query = query.filter_by(status=status)
    return [serializar_feedback(x) for x in query.order_by(FeedbackDB.id_feedback.desc()).all()]

def analisar_feedback(feedback_id: int, status: str, db: Session):
    item = db.get(FeedbackDB, feedback_id)
    if not item: raise HTTPException(404, "Feedback não encontrado.")
    if status == "aprovado" and not item.autoriza_publicacao:
        raise HTTPException(409, "Este usuário não autorizou a publicação do comentário.")
    item.status = status
    item.analisado_em = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return serializar_feedback(item)

@router.post("/feedbacks/{feedback_id}/aprovar")
def aprovar_feedback(feedback_id: int, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    return analisar_feedback(feedback_id, "aprovado", db)

@router.post("/feedbacks/{feedback_id}/recusar")
def recusar_feedback(feedback_id: int, db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    return analisar_feedback(feedback_id, "recusado", db)

@router.get("/mentoria-avaliacoes")
def listar_avaliacoes_mentoria(db: Session = Depends(get_db), _: AdminSessionDB = Depends(admin_atual)):
    itens = db.query(MentoriaAvaliacaoDB, MentoriaTrilhaDB, MentorDB, EmpreendedorDB).join(
        MentoriaTrilhaDB, MentoriaTrilhaDB.id == MentoriaAvaliacaoDB.id_trilha).join(
        MentorDB, MentorDB.id_mentor == MentoriaAvaliacaoDB.id_mentor).join(
        EmpreendedorDB, EmpreendedorDB.id_empreendedor == MentoriaAvaliacaoDB.id_empreendedor).order_by(
        MentoriaAvaliacaoDB.id.desc()).all()
    return [{"id": a.id, "trilha_titulo": t.titulo, "mentor_nome": m.nome,
             "empreendedor_nome": e.nome, "nota_trilha": a.nota_trilha,
             "nota_mentor": a.nota_mentor, "comentario": a.comentario,
             "criada_em": a.criada_em} for a, t, m, e in itens]
