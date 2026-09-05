from pydantic import BaseModel
from typing import Optional
from datetime import date

class EmpresaPorIdResponse(BaseModel):
    id_empresa: int
    nome: str
    data_fundacao: date
    cnpj: str
    segmento: str
    endereco: str
    porte: str
    num_funcionarios: int
    faturamento_meta_mensal: float
    saldo_atual: float

    class Config:
        from_attributes = True

class EmpresaAtualizar(BaseModel):
    nome: Optional[str] = None
    data_fundacao: Optional[date] = None
    cnpj: Optional[str] = None
    segmento: Optional[str] = None
    endereco: Optional[str] = None
    porte: Optional[str] = None
    num_funcionarios: Optional[int] = None
    faturamento_meta_mensal: Optional[float] = None
    saldo_atual: Optional[float] = None

class EmpresaAtualizarResponse(BaseModel):
    id_empresa: int
    nome: Optional[str] = None
    data_fundacao: Optional[date] = None
    cnpj: Optional[str] = None
    segmento: Optional[str] = None
    endereco: Optional[str] = None
    porte: Optional[str] = None
    num_funcionarios: Optional[int] = None
    faturamento_meta_mensal: Optional[float] = None
    saldo_atual: Optional[float] = None

    class Config:
        from_attributes = True