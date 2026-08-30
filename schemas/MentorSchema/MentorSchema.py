from pydantic import BaseModel
from typing import Optional

class MentorPorIdResponse(BaseModel):
    id_mentor: int
    nome: str
    especialidade: str 
    biografia: str

    class Config:
        from_attributes = True

class MentorAtualizar(BaseModel):
    nome: Optional[str] = None
    especialidade: Optional[str] = None 
    biografia: Optional[str] = None

class MentorAtualizarResponse(BaseModel):
    id_atividade: int
    nome: Optional[str] = None
    especialidade: Optional[str] = None 
    biografia: Optional[str] = None

    class Config:
        from_attributes = True