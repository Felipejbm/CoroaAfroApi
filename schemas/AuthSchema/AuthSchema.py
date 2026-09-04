from datetime import datetime
from pydantic import BaseModel, ConfigDict


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