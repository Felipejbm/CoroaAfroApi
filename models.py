from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Date, Text, ForeignKey
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
    
class EmpresaDB(Base):
    __tablename__= "empresa"

    id_empresa = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    data_fundacao = Column(Date, nullable=False) 
    cnpj = Column(String(14), nullable=False)
    segmento= Column(String(20), nullable=False)
    endereco = Column(String(255), nullable=False)
    porte = Column(String(10), nullable=False)
    num_funcionarios = Column(Integer, nullable=False)

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
