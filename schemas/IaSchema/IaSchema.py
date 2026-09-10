from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IaConversaCriar(BaseModel):
    titulo: str = Field(default="Nova conversa", min_length=1, max_length=120)

    @field_validator("titulo")
    @classmethod
    def limpar_titulo(cls, titulo: str) -> str:
        return titulo.strip()


class IaConversaAtualizar(BaseModel):
    titulo: str = Field(min_length=1, max_length=120)

    @field_validator("titulo")
    @classmethod
    def limpar_titulo(cls, titulo: str) -> str:
        titulo = titulo.strip()
        if not titulo:
            raise ValueError("O título não pode estar vazio.")
        return titulo


class IaMensagemCriar(BaseModel):
    conteudo: str = Field(min_length=1, max_length=4000)
    modo: Literal[
        "diagnostico_completo",
        "geral",
        "analisar_instagram",
        "calendario_conteudo",
        "ideias_posts",
        "criar_legenda",
        "analisar_metas",
        "orientar_trilhas",
        "preparar_mentor",
    ] = "geral"

    @field_validator("conteudo")
    @classmethod
    def limpar_conteudo(cls, conteudo: str) -> str:
        conteudo = conteudo.strip()
        if not conteudo:
            raise ValueError("A mensagem não pode estar vazia.")
        return conteudo


class IaConversaPublica(BaseModel):
    id_conversa: int
    titulo: str
    criada_em: datetime
    atualizada_em: datetime
    arquivada: bool

    model_config = ConfigDict(from_attributes=True)


class IaMensagemPublica(BaseModel):
    id_mensagem: int
    id_conversa: int
    papel: Literal["usuario", "assistente"]
    conteudo: str
    criada_em: datetime

    model_config = ConfigDict(from_attributes=True)


class IaResposta(BaseModel):
    conversa: IaConversaPublica
    mensagem_usuario: IaMensagemPublica
    mensagem_assistente: IaMensagemPublica
    fontes_contexto: list[str] = Field(default_factory=list)
