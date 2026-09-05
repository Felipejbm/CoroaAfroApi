from pydantic import BaseModel
from typing import Optional
from datetime import date

class TrilhaPorIdResponse(BaseModel):
    id_trilha: int
    titulo: str
    tipo_trilha: str 

    class Config:
        from_attributes = True

class TrilhaAtualizar(BaseModel):
    titulo: Optional[str] = None
    tipo_trilha: Optional[str] = None

class TrilhaAtualizarResponse(BaseModel):
    id_trilha: int
    titulo: Optional[str] = None
    tipo_trilha: Optional[str] = None

    class Config:
        from_attributes = True