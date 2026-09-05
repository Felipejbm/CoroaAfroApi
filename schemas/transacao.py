from pydantic import BaseModel
from typing import Optional
from datetime import date

class TransacaoPorIdResponse(BaseModel):
    id_transacao: int
    tipo_transacao: str
    valor: float
    data: date
    status: str

    class Config:
        from_attributes = True

class TransacaoAtualizar(BaseModel):
    tipo_transacao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[date] = None
    status: Optional[str] = None

class TransacaoAtualizarResponse(BaseModel):
    id_transacao: int
    tipo_transacao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[date] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True
