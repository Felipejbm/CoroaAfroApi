import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from models import EmpresaDB, EmpresaEmpreendedorDB, EmpreendedorDB
from dependencies import get_current_user
from company_options import NICHOS, PORTES, UFS
from services.company_identity import criar_vinculo_usuario

router = APIRouter(prefix="/empresa", tags=["Empresa"])

class EmpresaEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    nome: str = Field(min_length=1, max_length=150)
    nome_fantasia: str = Field(default="", max_length=150)
    data_fundacao: date
    cnpj: str = ""
    segmento: str
    porte: str
    num_funcionarios: int = Field(ge=0, le=1_000_000)
    rua: str = Field(min_length=1, max_length=150)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str = Field(default="", max_length=100)
    bairro: str = Field(min_length=1, max_length=100)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str
    cep: str = ""

    @field_validator("segmento")
    @classmethod
    def validar_segmento(cls, value):
        if value not in NICHOS:
            raise ValueError("Escolha um nicho da lista.")
        return value

    @field_validator("porte")
    @classmethod
    def validar_porte(cls, value):
        if value not in PORTES:
            raise ValueError("Escolha um porte/enquadramento da lista.")
        return value

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, value):
        if value not in UFS:
            raise ValueError("Selecione uma UF válida.")
        return value

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, value):
        value = value.replace("-", "").replace(" ", "")
        if value and not re.fullmatch(r"[0-9]{8}", value):
            raise ValueError("Informe um CEP com 8 números ou deixe em branco.")
        return value

    @field_validator("cnpj")
    @classmethod
    def normalizar_cnpj(cls, value):
        value = re.sub(r"[./\s-]", "", value).upper()
        if value and not re.fullmatch(r"[A-Z0-9]{14}", value):
            raise ValueError("Informe um CNPJ com 14 caracteres ou deixe em branco.")
        return value

    @field_validator("data_fundacao")
    @classmethod
    def validar_data(cls, value):
        if value > date.today():
            raise ValueError("A data de fundação não pode estar no futuro.")
        return value


def saida(empresa):
    result = {field: getattr(empresa, field) for field in EmpresaEntrada.model_fields}
    for field in ("nome_fantasia", "cnpj", "segmento", "porte", "rua", "numero", "complemento", "bairro", "cidade", "estado", "cep"):
        result[field] = result[field] or ""
    result["id_empresa"] = empresa.id_empresa
    result["segmento_label"] = NICHOS.get(empresa.segmento, empresa.segmento or "Não informado")
    result["porte_label"] = PORTES.get(empresa.porte, empresa.porte or "Não informado")
    result["endereco_legado"] = empresa.endereco or ""
    result["endereco"] = ", ".join(filter(None, [empresa.rua, empresa.numero, empresa.complemento,
        empresa.bairro, empresa.cidade, empresa.estado, empresa.cep])) if empresa.rua else empresa.endereco or "Não informado"
    return result


def minha_empresa(db, user):
    link = db.get(EmpresaEmpreendedorDB, user.id_empreendedor)
    empresa = db.get(EmpresaDB, link.id_empresa) if link else None
    if not empresa:
        raise HTTPException(404, "Você ainda não cadastrou sua empresa.")
    return empresa


@router.get("/opcoes")
def opcoes(user: EmpreendedorDB = Depends(get_current_user)):
    return {"nichos": [{"valor": key, "label": label} for key, label in NICHOS.items()],
            "portes": [{"valor": key, "label": label} for key, label in PORTES.items()], "estados": UFS}


@router.post("/criar-empresa", status_code=201)
def criar_empresa(empresa: EmpresaEntrada, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    if db.get(EmpresaEmpreendedorDB, user.id_empreendedor):
        raise HTTPException(409, "Você já tem uma empresa cadastrada. Edite os dados existentes.")
    try:
        usuario = criar_vinculo_usuario(db, user)
        dados = empresa.model_dump()
        dados["cnpj"] = dados["cnpj"] or None

        nova = EmpresaDB(
            **dados, 
            fk_empreendedor_id_empreendedor=user.id_empreendedor
        )
        db.add(nova)
        db.flush()
        db.add(EmpresaEmpreendedorDB(id_empreendedor=user.id_empreendedor, id_empresa=nova.id_empresa))
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(409, f"Não foi possível cadastrar: {e.orig}")
    except HTTPException:
        db.rollback()
        raise

    db.refresh(nova)
    return {"Msg": "Empresa criada com sucesso!", "Empresa": saida(nova)}


@router.get("/minha")
def obter_minha_empresa(response: Response, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return saida(minha_empresa(db, user))


@router.get("")
def listar_empresas(db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    link = db.get(EmpresaEmpreendedorDB, user.id_empreendedor)
    empresa = db.get(EmpresaDB, link.id_empresa) if link else None
    return [saida(empresa)] if empresa else []


@router.get("/{id_empresa}")
def obter_empresa_por_id(id_empresa: int, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    empresa = minha_empresa(db, user)
    if empresa.id_empresa != id_empresa:
        raise HTTPException(404, "Empresa não encontrada.")
    return saida(empresa)


@router.patch("/{id_empresa}")
def atualizar_empresa(id_empresa: int, dados: EmpresaEntrada, db: Session = Depends(get_db), user: EmpreendedorDB = Depends(get_current_user)):
    empresa = minha_empresa(db, user)
    if empresa.id_empresa != id_empresa:
        raise HTTPException(404, "Empresa não encontrada.")
    for field, value in dados.model_dump().items():
        setattr(empresa, field, (value or None) if field == "cnpj" else value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma empresa com esse CNPJ.")
    db.refresh(empresa)
    return saida(empresa)

