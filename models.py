from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime 

from database import Base


class Empreendedor(Base):
    __tablename__= "empreendedor"

    id_empreendedor = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now, nullable=False)