from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal
from pydantic import BaseModel, Field

class EmpreendedorPublic(BaseModel):
    id_empreendedor: int
    nome: str
    email: str
    telefone: str | None = None
    data_cadastro: datetime
    papel: str = "empreendedor"

    model_config = ConfigDict(from_attributes=True)

class MentorPublic(BaseModel):
    id: int
    nome: str
    email: str
    especialidade: str | None = None
    biografia: str | None = None
    papel: str = "mentor"

    model_config = ConfigDict(from_attributes=True)

class LoginReq(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    senha: str = Field(min_length=1, max_length=1024)
    papel: Literal["empreendedor", "mentor"] = "empreendedor"