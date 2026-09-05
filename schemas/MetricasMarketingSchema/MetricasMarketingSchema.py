from pydantic import BaseModel
from typing import Optional
from datetime import date

class MetricasMarketingPorIdResponse(BaseModel):
    id_metrica: int
    data_coleta: date
    seguidores_total: int
    alcance_postagem: int
    engajamento_taxa: int
    cliques_bio: int

    class Config:
        from_attributes = True

class MetricasMarketingAtualizar(BaseModel):
    data_coleta: Optional[date] = None
    seguidores_total: Optional[int] = None
    alcance_postagem: Optional[int] = None
    engajamento_taxa: Optional[int] = None
    cliques_bio: Optional[int] = None

class MetricasMarketingAtualizarResponse(BaseModel):
    id_atividade: int
    data_coleta: Optional[date] = None
    seguidores_total: Optional[int] = None
    alcance_postagem: Optional[int] = None
    engajamento_taxa: Optional[int] = None
    cliques_bio: Optional[int] = None

    class Config:
        from_attributes = True

class MetricasMarketingCreate(BaseModel):
    data_coleta: date
    seguidores_total: int
    alcance_postagem: int
    engajamento_taxa: int
    cliques_bio: int