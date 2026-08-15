from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import MetricasMarketing
from schemas import MetricasMarketingCreate

router = APIRouter(
    prefix="/metricas",
    tags=["Metricas"]
)

@router.post('/buscar-metricas-marketing')
def buscar_metricas_marketing(metricas: MetricasMarketingCreate, db: Session = Depends(get_db)):
    novas_metricas = MetricasMarketing(
        data_coleta = metricas.data_coleta,
        seguidores_total = metricas.seguidores_total,
        alcance_postagem = metricas.alcance_postagem,
        engajamento_taxa = metricas.engajamento_taxa,
        cliques_bio = metricas.cliques_bio
    )

    db.add(novas_metricas)
    db.commit()
    db.refresh(novas_metricas)

    return{
        "Msg": "Métricas atualizadas com sucesso!",
        "Empreendedor": novas_metricas
    }