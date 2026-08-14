from pydantic import BaseModel
from datetime import date

class LoginReq(BaseModel):
    email: str
    senha: str

class EmpreendedorCreate(BaseModel):
    nome: str
    email: str
    senha: str
    genero: str
    telefone: str
    data_cadastro: date
    data_nascimento: date

class EmpresaCreate(BaseModel):
    nome: str
    data_fundacao: date
    cnpj: str
    segmento: str
    endereco: str
    porte: str
    num_funcionarios: int

