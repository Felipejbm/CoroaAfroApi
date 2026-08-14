from sqlalchemy import Column, Integer, String, DateTime, Date
from datetime import datetime 

from database import Base


class Empreendedor(Base):
    __tablename__= "empreendedor"

    id_empreendedor = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    senha = Column(String, nullable=False)
    data_nascimento = Column(Date, nullable=False) 
    email = Column(String, unique=True, nullable=False)
    cpf= Column(String, nullable=False)
    genero = Column(String, nullable=False)
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