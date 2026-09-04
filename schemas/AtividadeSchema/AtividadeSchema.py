from pydantic import BaseModel
from typing import Optional

class AtividadePorIdResponse(BaseModel):
    id_atividade: int
    titulo_tarefa: str
    conteudo: str

    class Config:
        from_attributes = True

class AtividadeAtualizar(BaseModel):
    titulo_tarefa: Optional[str] = None
    conteudo: Optional[str] = None

class AtividadeAtualizarResponse(BaseModel):
    id_atividade: int
    titulo_tarefa: Optional[str] = None
    conteudo: Optional[str] = None

    class Config:
        from_attributes = True

class AtividadeCreate(BaseModel):
    titulo_tarefa: str
    conteudo: str
