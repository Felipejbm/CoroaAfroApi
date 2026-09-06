from sqlalchemy import (
    Boolean, 
    Column, 
    Integer, 
    String, 
    DateTime, 
    Float, 
    Date, 
    Text, 
    ForeignKey, 
    Numeric, 
    ForeignKeyConstraint, 
    UniqueConstraint, 
    Index
    )
from datetime import datetime 
from database import Base

class EmpreendedorDB(Base):
    __tablename__= "empreendedor"

    id_empreendedor = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=False)
    
class UsuarioDB(Base):
    __tablename__ = "usuario"
    id_usuario = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    senha = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)
    cpf = Column(String(14), nullable=True, unique=True)
    genero = Column(String(30), nullable=True)
    data_nascimento = Column(Date, nullable=True)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=True)


class EmpreendedorUsuarioDB(Base):
    __tablename__ = "empreendedor_usuario"
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False, unique=True)

class EmpresaDB(Base):
    __tablename__= "empresa"

    id_empresa = Column(Integer, primary_key=True, index=True)
    fk_empreendedor_id_empreendedor = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    nome = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150), nullable=True)
    data_fundacao = Column(Date, nullable=True)
    cnpj = Column(String(18), nullable=True, unique=True)
    segmento = Column(String(32), nullable=True)
    endereco = Column(String(255), nullable=True)
    porte = Column(String(50), nullable=True)
    num_funcionarios = Column(Integer, nullable=True)
    rua = Column(String(150), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    cep = Column(String(8), nullable=True)
    
class EmpresaEmpreendedorDB(Base):
    __tablename__ = "empresa_empreendedor"

    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresa.id_empresa"), nullable=False, unique=True)

class AuthSessionDB(Base):
    __tablename__ = "auth_session"

    token_hash = Column(String(64), primary_key=True)
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    oauth_state_hash = Column(String(64), nullable=True)

class MentorAccessDB(Base):
    __tablename__ = "mentor_access"
    id_mentor = Column(Integer, ForeignKey("mentor.id_mentor"), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

class MentorSessionDB(Base):
    __tablename__ = "mentor_session"
    token_hash = Column(String(64), primary_key=True)
    id_mentor = Column(Integer, ForeignKey("mentor.id_mentor"), nullable=False)
    expires_at = Column(DateTime, nullable=False)

class MentoriaDB(Base):
    __tablename__ = "mentoria_vinculo"
    id_mentor = Column(Integer, ForeignKey("mentor.id_mentor"), primary_key=True)
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), primary_key=True)
    ativo = Column(Boolean, nullable=False, default=True)

class MetaEmpreendedorDB(Base):
    __tablename__ = "meta_empreendedor"
    id = Column(Integer, primary_key=True)
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), nullable=False, index=True)
    titulo = Column(String(120), nullable=False)
    unidade = Column(String(30), nullable=False)
    valor_inicial = Column(Numeric(14, 2), nullable=False)
    valor_atual = Column(Numeric(14, 2), nullable=False)
    valor_alvo = Column(Numeric(14, 2), nullable=False)
    prazo = Column(Date, nullable=False)
    arquivada = Column(Boolean, nullable=False, default=False)
    versao = Column(Integer, nullable=False, default=1)

class MentoriaTrilhaDB(Base):
    __tablename__ = "mentoria_trilha"
    id = Column(Integer, primary_key=True)
    id_mentor = Column(Integer, ForeignKey("mentor.id_mentor"), nullable=False, index=True)
    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    publicada = Column(Boolean, nullable=False, default=False)
    versao = Column(Integer, nullable=False, default=1)

class MentoriaCatalogoDB(Base):
    __tablename__ = "mentoria_catalogo"
    id_trilha = Column(Integer, ForeignKey("mentoria_trilha.id"), primary_key=True)
    categoria = Column(String(32), nullable=False, default="geral", index=True)
    publico_alvo = Column(String(500), nullable=False, default="")

class MentoriaAulaDB(Base):
    __tablename__ = "mentoria_aula"
    id = Column(Integer, primary_key=True)
    id_trilha = Column(Integer, ForeignKey("mentoria_trilha.id"), nullable=False, index=True)
    ordem = Column(Integer, nullable=False)
    titulo = Column(String(150), nullable=False)
    conteudo = Column(Text, nullable=False)
    video_url = Column(String(2048), nullable=True)

class MentoriaAtribuicaoDB(Base):
    __tablename__ = "mentoria_atribuicao"
    id_trilha = Column(Integer, ForeignKey("mentoria_trilha.id"), primary_key=True)
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), primary_key=True)

class MentoriaProgressoDB(Base):
    __tablename__ = "mentoria_progresso"
    id_aula = Column(Integer, ForeignKey("mentoria_aula.id"), primary_key=True)
    id_empreendedor = Column(Integer, ForeignKey("empreendedor.id_empreendedor"), primary_key=True)
    concluida = Column(Boolean, nullable=False, default=False)

class TrilhaDB(Base):
    __tablename__= "trilha"

    id_trilha = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    tipo_trilha = Column(String(255), unique=True, nullable=False)

class AtividadeDB(Base):
    __tablename__= "atividade"

    id_atividade = Column(Integer, primary_key=True, index=True)
    titulo_tarefa = Column(String(255), nullable=False)
    conteudo = Column(Text, nullable=False)

class MentorDB(Base):
    __tablename__= "mentor"

    id_mentor = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    especialidade = Column(String(50), nullable=False)
    biografia = Column(Text, nullable=False)

class MentoriaMensagemDB(Base):
    __tablename__ = "mentoria_mensagem"
    id = Column(Integer, primary_key=True)
    id_mentor = Column(Integer, nullable=False)
    id_empreendedor = Column(Integer, nullable=False)
    remetente = Column(String(20), nullable=False)
    texto = Column(Text, nullable=False)
    chave_envio = Column(String(36), nullable=False)
    criado_em = Column(DateTime, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["id_mentor", "id_empreendedor"],
                             ["mentoria_vinculo.id_mentor", "mentoria_vinculo.id_empreendedor"]),
        UniqueConstraint("id_mentor", "id_empreendedor", "remetente", "chave_envio", name="uq_chat_envio"),
        Index("ix_chat_conversa_id", "id_mentor", "id_empreendedor", "id"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

class MensagemChatDB(Base):
    __tablename__="mensagem_chat"

    id_mensagem = Column(Integer, primary_key=True, index=True)
    texto_mensagem = Column(Text, nullable=False)
    data_envio = Column(DateTime, default=datetime.now, nullable=False)
    lida = Column(Boolean, nullable=False, default=False)
    remetente = Column(String(20), nullable=False)

class PostagemChatDB(Base):
    __tablename__ = "postagem"

    id_post = Column(Integer, primary_key=True, index=True)
    conteudo_texto = Column(Text, nullable=False)
    midia_url = Column(String(2048))
    data_publicacao = Column(DateTime, default=datetime.now, nullable=False)

class TransacaoDB(Base):
    __tablename__ = "transacoes"

    id_transacao = Column(Integer, primary_key=True, index=True)
    tipo_transacao = Column(String(15), nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="Pendente")

class SaldoDB(Base):
    __tablename__ = "saldo"

    id_saldo = Column(Integer, primary_key=True, index=True)
    saldo = Column(Float, nullable=False)
    meta_faturamento = Column(Float, nullable=False)
    data = Column(DateTime, nullable=False)
    total_entradas = Column(Integer, nullable=False)
    total_saidas = Column(Integer, nullable=False)
    valor_inicial = Column(Float, nullable=False)
    saldo_final = Column(Float, nullable=False)

class MetricasMarketingDB(Base):
    __tablename__ = "metricas_marketing"

    id_metrica = Column(Integer, primary_key=True, index=True)
    data_coleta = Column(DateTime,default=datetime.now, nullable=False)
    seguidores_total = Column(Integer, nullable=False)
    alcance_postagem = Column(Integer, nullable=False)
    engajamento_taxa = Column(Integer, nullable=False)
    cliques_bio = Column(Integer, nullable=False)

class MetaInstagramConnectionDB(Base):
    __tablename__ = "meta_instagram_connection"

    id_conexao = Column(Integer, primary_key=True, index=True)
    id_empreendedor = Column(
        Integer,
        ForeignKey("empreendedor.id_empreendedor", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    facebook_page_id = Column(String(64), nullable=False)
    facebook_page_name = Column(String(255), nullable=False)
    instagram_business_account_id = Column(String(64), nullable=False, index=True)
    access_token_encrypted = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )