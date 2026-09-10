from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

ValorDecimal = Annotated[Decimal, Field(max_digits=5, decimal_places=2, allow_inf_nan=False)]

class MetricasMarketingPorIdResponse(BaseModel):
    id_metrica: int
    data_coleta: date
    seguidores_total: int
    alcance_postagem: int
    engajamento_taxa: ValorDecimal
    cliques_bio: int

    class Config:
        from_attributes = True

class MetricasMarketingAtualizar(BaseModel):
    data_coleta: Optional[date] = None
    seguidores_total: Optional[int] = None
    alcance_postagem: Optional[int] = None
    engajamento_taxa: Optional[ValorDecimal] = None
    cliques_bio: Optional[int] = None

class MetricasMarketingAtualizarResponse(BaseModel):
    id_metrica: int
    data_coleta: Optional[date] = None
    seguidores_total: Optional[int] = None
    alcance_postagem: Optional[int] = None
    engajamento_taxa: Optional[ValorDecimal] = None
    cliques_bio: Optional[int] = None

    class Config:
        from_attributes = True

class MetricasMarketingCreate(BaseModel):
    data_coleta: date
    seguidores_total: int
    alcance_postagem: int
    engajamento_taxa: ValorDecimal
    cliques_bio: int