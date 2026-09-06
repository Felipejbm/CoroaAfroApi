from datetime import date
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator, model_validator

TextoPost = Annotated[str, Field(min_length=1, max_length=4000)]

class Entrada(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class PostagemChatCreate(Entrada):
    conteudo_texto: TextoPost
    midia_url: str | None = Field(default=None, max_length=255)

    @field_validator('midia_url')
    @classmethod
    def validar_url(cls, valor):
        if not valor:
            return None
        url = TypeAdapter(HttpUrl).validate_python(valor)
        if url.username or url.password:
            raise ValueError('A URL não pode conter credenciais.')
        return valor

class PostagemAtualizar(PostagemChatCreate):
    conteudo_texto: TextoPost | None = None

    @model_validator(mode='after')
    def validar_alteracao(self):
        if not self.model_fields_set or ('conteudo_texto' in self.model_fields_set and self.conteudo_texto is None):
            raise ValueError('Informe um texto válido ou uma alteração de imagem.')
        return self

class ComentarioCreate(Entrada):
    texto: str = Field(min_length=1, max_length=2000)

class ComentarioResponse(BaseModel):
    id: int
    author: str
    text: str
    autorId: int
    autorPapel: str = 'empreendedor'

class PostagemPorIdResponse(BaseModel):
    id_post: int
    conteudo_texto: str
    midia_url: str | None
    data_publicacao: date
    autor_id: int
    autor_papel: str
    autor_foto_url: str | None = None
    minha: bool
    imagem_upload_url: str | None = None
    company: str
    segment: str
    comments: list[ComentarioResponse]

PostagemAtualizarResponse = PostagemPorIdResponse
