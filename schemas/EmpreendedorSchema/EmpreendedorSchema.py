from pydantic import BaseModel
from typing import Optional
from datetime import date

class EmpreendedorPorIdResponse(BaseModel):
    id_empreendedor: int
    nome: str
    email: str
    telefone: str
    data_cadastro: date


    class Config:
        from_attributes = True

class EmpreendedorAtualizar(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

class EmpreendedorAtualizarResponse(BaseModel):
    id_empreendedor: int
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

    class Config:
        from_attributes = True

class EmpreendedorCreate(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str
    data_cadastro: date