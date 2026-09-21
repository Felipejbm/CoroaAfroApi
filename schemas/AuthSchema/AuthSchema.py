from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class EmpreendedorPublic(BaseModel):
    id: int = Field(validation_alias="id_empreendedor")
    nome: str
    email: str
    telefone: str | None = None
    data_cadastro: datetime
    papel: str = "empreendedor"
    foto_perfil_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class MentorPublic(BaseModel):
    administrador: bool = False
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

class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    papel: Literal["empreendedor", "mentor"] = "empreendedor"

class PasswordResetConfirm(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    papel: Literal["empreendedor", "mentor"] = "empreendedor"
    codigo: str = Field(pattern=r"^\d{6}$")
    nova_senha: str = Field(min_length=8, max_length=128)


class SocialSignupPublic(BaseModel):
    provider: Literal["google", "linkedin"]
    nome: str
    email: str


class SocialSignupComplete(BaseModel):
    telefone: str = Field(min_length=8, max_length=20)
    cpf: str | None = Field(default=None, max_length=14)
    genero: str | None = Field(default=None, max_length=30)
    data_nascimento: date | None = None
