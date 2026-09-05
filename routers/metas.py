from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session
from database import get_db
from models import EmpreendedorDB, MetaEmpreendedorDB
from security import get_current_user

router = APIRouter(prefix="/metas", tags=["Metas"])


class MetaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=120)
    unidade: str = Field(min_length=1, max_length=30)
    valor_inicial: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    valor_atual: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    valor_alvo: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    prazo: date
    arquivada: bool = False

    @model_validator(mode="after")
    def validar_alvo(self):
        if self.valor_alvo <= self.valor_inicial:
            raise ValueError("O alvo deve ser maior que o valor inicial.")
        return self


class MetaEdicao(MetaEntrada):
    versao: int = Field(ge=1)


def saida(meta):
    progresso = max(Decimal(0), min(Decimal(100),
        (meta.valor_atual - meta.valor_inicial) * 100 / (meta.valor_alvo - meta.valor_inicial)))
    status = ("arquivada" if meta.arquivada else "atingida" if meta.valor_atual >= meta.valor_alvo
              else "prazo_encerrado" if meta.prazo < date.today() else "em_andamento")
    return {**{field: getattr(meta, field) for field in MetaEntrada.model_fields},
            "id": meta.id, "versao": meta.versao, "progresso": float(round(progresso, 2)),
            "status": status, "origem": "manual"}


@router.get("")
def listar(response: Response, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    metas = db.query(MetaEmpreendedorDB).filter_by(id_empreendedor=user.id_empreendedor).order_by(MetaEmpreendedorDB.id.desc()).all()
    return [saida(meta) for meta in metas]


@router.post("", status_code=201)
def criar(dados: MetaEntrada, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    meta = MetaEmpreendedorDB(**dados.model_dump(), id_empreendedor=user.id_empreendedor)
    db.add(meta); db.commit(); db.refresh(meta)
    return saida(meta)


@router.patch("/{id_meta}")
def editar(id_meta: int, dados: MetaEdicao, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    query = db.query(MetaEmpreendedorDB).filter_by(id=id_meta, id_empreendedor=user.id_empreendedor)
    if not query.first():
        raise HTTPException(404, "Meta não encontrada.")
    updated = query.filter_by(versao=dados.versao).update(
        {**dados.model_dump(exclude={"versao"}), "versao": dados.versao + 1}, synchronize_session=False)
    if not updated:
        db.rollback()
        raise HTTPException(409, "Esta meta mudou em outra tela. Atualize a lista antes de editar novamente.")
    db.commit()
    return saida(query.first())

