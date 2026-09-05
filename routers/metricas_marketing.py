from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import MetricasMarketingDB
from schemas.common import MetricasMarketingCreate
from schemas.metricas_marketing import (
    MetricasMarketingPorIdResponse,
    MetricasMarketingAtualizarResponse,
    MetricasMarketingAtualizar
)

router = APIRouter(
    prefix="/metricas",
    tags=["Metricas"]
)

@router.post('/buscar-metricas-marketing')
def buscar_metricas_marketing(metricas: MetricasMarketingCreate, db: Session = Depends(get_db)):
    novas_metricas = MetricasMarketingDB(
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

@router.get('')
def listar_metricas(db: Session = Depends(get_db)):
    metricas_banco = db.query(MetricasMarketingDB).all()

    return metricas_banco

@router.get('/{id_metrica}', response_model=MetricasMarketingPorIdResponse)
def obter_metricas_por_id(id_metrica: int, db: Session = Depends(get_db)):
    metricas_banco = db.query(MetricasMarketingDB).filter(MetricasMarketingDB.id_metrica == id_metrica).first()

    if not metricas_banco:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    return  metricas_banco

