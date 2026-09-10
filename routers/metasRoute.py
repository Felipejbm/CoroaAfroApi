from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session
from database import get_db
from models import EmpreendedorDB, MetaEmpreendedorDB
from dependencies import get_current_user
from services.ia_contexto import _contexto_instagram

router = APIRouter(prefix="/metas", tags=["Metas"])

METRICAS_INSTAGRAM = {
    "seguidores": "seguidores",
    "publicacoes": "publicações",
    "alcance_7d": "contas alcançadas em 7 dias",
    "interacoes_recentes": "interações",
}


class MetaEntrada(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def unidade_automatica(cls, dados):
        if isinstance(dados, dict) and dados.get("tipo") == "instagram" and dados.get("metrica") in METRICAS_INSTAGRAM:
            return {**dados, "unidade": METRICAS_INSTAGRAM[dados["metrica"]]}
        return dados

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=120)
    unidade: str = Field(min_length=1, max_length=30)
    valor_inicial: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    valor_atual: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    valor_alvo: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    prazo: date | None = None
    arquivada: bool = False
    tipo: Literal["manual", "instagram"] = "manual"
    origem: Literal["manual", "ia"] = "manual"
    metrica: Literal["seguidores", "publicacoes", "alcance_7d", "interacoes_recentes"] | None = None

    @model_validator(mode="after")
    def validar_alvo(self):
        if self.tipo == "instagram" and not self.metrica:
            raise ValueError("Escolha a métrica do Instagram.")
        if self.valor_alvo <= self.valor_inicial:
            raise ValueError("O alvo deve ser maior que o valor inicial.")
        return self


class MetaEdicao(MetaEntrada):
    versao: int = Field(ge=1)


def saida(meta):
    progresso = max(Decimal(0), min(Decimal(100),
        (meta.valor_atual - meta.valor_inicial) * 100 / (meta.valor_alvo - meta.valor_inicial)))
    status = ("arquivada" if meta.arquivada else "atingida" if meta.valor_atual >= meta.valor_alvo
              else "prazo_encerrado" if meta.prazo and meta.prazo < date.today() else "em_andamento")
    return {**{field: getattr(meta, field) for field in MetaEntrada.model_fields},
            "id": meta.id, "versao": meta.versao, "progresso": float(round(progresso, 2)),
            "status": status, "origem": meta.origem,
            "ultima_sincronizacao": meta.ultima_sincronizacao}


async def valores_reais_instagram(user, db):
    contexto = await _contexto_instagram(user, db)
    if not contexto.get("dados_disponiveis"):
        return None
    publicacoes = contexto.get("publicacoes_recentes") or []
    return {
        "seguidores": Decimal(contexto.get("seguidores") or 0),
        "publicacoes": Decimal(contexto.get("quantidade_publicacoes") or 0),
        "alcance_7d": Decimal(sum(
            item.get("valor") or 0 for item in contexto.get("alcance_diario_recente") or []
        )),
        "interacoes_recentes": Decimal(sum(
            item.get("interacoes_calculadas") or 0 for item in publicacoes
        )),
    }


@router.get("")
async def listar(response: Response, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    metas = db.query(MetaEmpreendedorDB).filter_by(id_empreendedor=user.id_empreendedor).order_by(MetaEmpreendedorDB.id.desc()).all()
    automaticas = [meta for meta in metas if meta.tipo == "instagram" and not meta.arquivada]
    if automaticas:
        valores = await valores_reais_instagram(user, db)
        if valores:
            agora = datetime.now()
            for meta in automaticas:
                if meta.metrica in valores:
                    meta.valor_atual = valores[meta.metrica]
                    meta.ultima_sincronizacao = agora
            db.commit()
    return [saida(meta) for meta in metas]


@router.post("", status_code=201)
async def criar(dados: MetaEntrada, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    valores = dados.model_dump()
    if dados.tipo == "instagram":
        metricas = await valores_reais_instagram(user, db)
        if not metricas:
            raise HTTPException(409, "Conecte novamente o Instagram para criar uma meta automática.")
        atual = metricas[dados.metrica]
        if dados.valor_alvo <= atual:
            raise HTTPException(422, "O valor-alvo deve ser maior que o valor atual do Instagram.")
        valores.update(
            unidade=METRICAS_INSTAGRAM[dados.metrica],
            valor_inicial=atual,
            valor_atual=atual,
            ultima_sincronizacao=datetime.now(),
        )
    meta = MetaEmpreendedorDB(**valores, id_empreendedor=user.id_empreendedor)
    db.add(meta); db.commit(); db.refresh(meta)
    return saida(meta)


@router.patch("/{id_meta}")
def editar(id_meta: int, dados: MetaEdicao, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    query = db.query(MetaEmpreendedorDB).filter_by(id=id_meta, id_empreendedor=user.id_empreendedor)
    if not query.first():
        raise HTTPException(404, "Meta não encontrada.")
    atual = query.first()
    if dados.tipo != atual.tipo:
        raise HTTPException(422, "O tipo da meta não pode ser alterado. Crie uma nova meta.")
    alteracoes = dados.model_dump(exclude={"versao"})
    if atual.tipo == "instagram":
        if dados.valor_alvo <= atual.valor_inicial:
            raise HTTPException(422, "O alvo deve ser maior que o valor inicial registrado no Instagram.")
        for campo in ("tipo", "metrica", "unidade", "valor_inicial", "valor_atual"):
            alteracoes.pop(campo, None)
    updated = query.filter_by(versao=dados.versao).update(
        {**alteracoes, "versao": dados.versao + 1}, synchronize_session=False)
    if not updated:
        db.rollback()
        raise HTTPException(409, "Esta meta mudou em outra tela. Atualize a lista antes de editar novamente.")
    db.commit()
    return saida(query.first())
