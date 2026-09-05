from pydantic import BaseModel
from typing import Optional
from datetime import date

class SaldoPorIdResponse(BaseModel):
    id_saldo: int
    saldo: float
    meta_faturamento: float
    data: date
    total_entradas: int 
    total_saidas: int
    valor_inicial: float
    saldo_final: float

    class Config:
        from_attributes = True

class SaldoAtualizar(BaseModel):
    saldo: Optional[float] = None
    meta_faturamento: Optional[float] = None
    total_entradas: Optional[int] = None 
    total_saidas: Optional[int] = None
    valor_inicial: Optional[float] = None

class SaldoAtualizarResponse(BaseModel):
    id_saldo: int
    saldo: Optional[float] = None
    meta_faturamento: Optional[float] = None
    total_entradas: Optional[int] = None 
    total_saidas: Optional[int] = None
    valor_inicial: Optional[float] = None

    class Config:
        from_attributes = True
