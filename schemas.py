from pydantic import BaseModel
from datetime import date

class LoginReq(BaseModel):
    email: str
    senha: str

class EmpreendedorCreate(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str
    data_cadastro: date