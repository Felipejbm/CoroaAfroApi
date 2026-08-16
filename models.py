from sqlalchemy import Column, Integer, String, DateTime, Float, Date
from datetime import datetime 
from database import Base

class EmpreendedorDB(Base):
    __tablename__= "empreendedor"

    id_empreendedor = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=False)
    
class Empresa(Base):
    __tablename__= "empresa"

    id_empresa = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    data_fundacao = Column(Date, nullable=False) 
    cnpj = Column(String, nullable=False)
    segmento= Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    porte = Column(String, nullable=False)
    num_funcionarios = Column(Integer, nullable=False)

class Trilha(Base):
    __tablename__= "trilha"

    id_trilha = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    tipo_trilha = Column(String, unique=True, nullable=False)

class AtividadeDB(Base):
    __tablename__= "atividade"

    id_atividade = Column(Integer, primary_key=True, index=True)
    titulo_tarefa = Column(String, nullable=False)
    conteudo = Column(String, unique=True, nullable=False)

class MentorDB(Base):
    __tablename__= "mentor"

    id_mentor = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    especialidade = Column(String, nullable=False)
    biografia = Column(String, nullable=False)

class MensagemChatDB(Base):
    __tablename__="mensagem_chat"

    id_mensagem = Column(Integer, primary_key=True, index=True)
    texto_mensagem = Column(String, nullable=False)
    data_envio = Column(DateTime, default=datetime.now, nullable=False)
    lida = Column(String, nullable=False, default=False)
    remetente = Column(String, nullable=False)

class PostagemChatDB(Base):
    __tablename__ = "postagem"

    id_post = Column(Integer, primary_key=True, index=True)
    conteudo_texto = Column(String, nullable=False)
    midia_url = Column(String)
    data_publicacao = Column(DateTime, default=datetime.now, nullable=False)

class TransacaoDB(Base):
    __tablename__ = "transacoes"

    id_transacao = Column(Integer, primary_key=True, index=True)
    tipo_transacao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="Pendente")

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
