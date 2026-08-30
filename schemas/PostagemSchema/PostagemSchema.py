from pydantic import BaseModel
from typing import Optional

class PostagemPorIdResponse(BaseModel):
    id_post: int
    conteudo_texto: str 
    midia_url: str
    data_publicacao: str

    class Config:
        from_attributes = True

class PostagemAtualizar(BaseModel):
    conteudo_texto: Optional[str] = None
    midia_url: Optional[str] = None
    data_publicacao: Optional[str] = None

class PostagemAtualizarResponse(BaseModel):
    id_post: int
    conteudo_texto: Optional[str] = None
    midia_url: Optional[str] = None
    data_publicacao: Optional[str] = None

    class Config:
        from_attributes = True