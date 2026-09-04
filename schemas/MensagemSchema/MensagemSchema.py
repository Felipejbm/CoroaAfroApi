from pydantic import BaseModel
from typing import Optional
from datetime import date

class MensagemPorIdResponse(BaseModel):
    id_mensagem: int
    texto_mensagem: str
    data_envio: date
    lida: bool
    remetente: str

    class Config:
        from_attributes = True

class MensagemAtualizar(BaseModel):
    texto_mensagem: Optional[str] = None
    data_envio: Optional[date] = None
    lida: Optional[bool] = None
    remetente: Optional[str] = None

class MensagemAtualizarResponse(BaseModel):
    id_mensagem: int
    texto_mensagem: Optional[str] = None
    data_envio: Optional[date] = None
    lida: Optional[bool] = None
    remetente: Optional[str] = None

    class Config:
        from_attributes = True

class MensagemChatCreate(BaseModel):
    texto_mensagem: str
    data_envio: date
    lida: bool
    remetente: str