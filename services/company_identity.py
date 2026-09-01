from fastapi import HTTPException
from sqlalchemy import func
from models import UsuarioDB, EmpreendedorUsuarioDB


def usuario_vinculado(db, empreendedor):
    link = db.get(EmpreendedorUsuarioDB, empreendedor.id_empreendedor)
    return db.get(UsuarioDB, link.id_usuario) if link else None


def criar_vinculo_usuario(db, empreendedor):
    usuario = usuario_vinculado(db, empreendedor)
    if usuario:
        return usuario
    if len(empreendedor.nome) > 150 or len(empreendedor.email) > 150:
        raise HTTPException(422, "Atualize nome e e-mail no perfil: o banco aceita até 150 caracteres.")
    # E-mail coincidente não comprova identidade. Não reivindicar um usuário antigo.
    if db.query(UsuarioDB).filter(func.lower(UsuarioDB.email) == empreendedor.email.lower()).first():
        raise HTTPException(409, "Existe um cadastro antigo com este e-mail. A equipe precisa conferir o vínculo antes de cadastrar a empresa.")
    usuario = UsuarioDB(nome=empreendedor.nome, email=empreendedor.email, senha=empreendedor.senha,
                        telefone=empreendedor.telefone, data_cadastro=empreendedor.data_cadastro)
    db.add(usuario)
    db.flush()
    db.add(EmpreendedorUsuarioDB(id_empreendedor=empreendedor.id_empreendedor, id_usuario=usuario.id_usuario))
    db.flush()
    return usuario
