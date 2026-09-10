from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

ValorDecimal = Annotated[Decimal, Field(max_digits=10, decimal_places=2, allow_inf_nan=False)]

class TransacaoPorIdResponse(BaseModel):
    id_transacao: int
    tipo_transacao: str
    valor: ValorDecimal
    data: date
    status: str

    class Config:
        from_attributes = True

class TransacaoAtualizar(BaseModel):
    tipo_transacao: Optional[str] = None
    valor: Optional[ValorDecimal] = None
    data: Optional[date] = None
    status: Optional[str] = None

class TransacaoAtualizarResponse(BaseModel):
    id_transacao: int
    tipo_transacao: Optional[str] = None
    valor: Optional[ValorDecimal] = None
    data: Optional[date] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class TransacoesCreate(BaseModel):
    tipo_transacao: str
    valor: ValorDecimal
    data: date
    status: str