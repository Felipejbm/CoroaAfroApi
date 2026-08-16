from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import EmpresaDB
from schemas.database.schemas import EmpresaCreate
from schemas.EmpresaSchema.EmpresaSchema import (
    EmpresaAtualizar,
    EmpresaPorIdResponse,
    EmpresaAtualizarResponse
    ) 

router = APIRouter(
    prefix="/empresa",
    tags=["Empresa"]
)

@router.post('/criar-empresa')
def criar_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    nova_empresa = EmpresaDB(
        nome = empresa.nome,
        data_fundacao = empresa.data_fundacao,
        cnpj = empresa.cnpj,
        segmento = empresa.segmento,
        endereco = empresa.endereco,
        porte = empresa.porte,
        num_funcionarios = empresa.num_funcionarios,
        faturamento_meta_mensal = empresa.faturamento_meta_mensal,
        saldo_atual = empresa.saldo_atual
    )

    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)

    return{
        "Msg": "Empresa criada com sucesso!",
        "Empresa": nova_empresa

    } 

@router.get('')
def listar_empresas(db: Session = Depends(get_db)):
    empresas_banco = db.query(EmpresaDB).all()

    return empresas_banco

@router.get('/{id_empresa}', response_model=EmpresaPorIdResponse)
def obter_empresa_por_id(id_empresa: int, db: Session = Depends(get_db)):
    empresa_banco = db.query(EmpresaDB).filter(EmpresaDB.id_empresa == id_empresa).first()

    if not empresa_banco:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return  empresa_banco

@router.patch('/{id_empresa}', response_model=EmpresaAtualizarResponse)
def atualizar_empresa(
        id_empresa: int, 
        empresa_data: EmpresaAtualizar,
        db: Session = Depends(get_db) 
        ):
    empresa_banco = db.query(EmpresaDB).filter(EmpresaDB.id_empresa == id_empresa).first()

    if not empresa_banco:
        raise HTTPException(status_code=404, detail=("Empresa não encontrada"))

    empresa_atualizada = empresa_data.model_dump(exclude_unset=True)

    for chave, valor in empresa_atualizada.items():
        setattr(empresa_banco, chave, valor)

    db.commit()
    db.refresh(empresa_banco)

    return empresa_banco

@router.delete('/{id_empresa}')
def deletar_empresa(id_empresa: int, db: Session = Depends(get_db)):
    empresa_banco = db.query(EmpresaDB).filter(EmpresaDB.id_empresa == id_empresa). first()

    if not empresa_banco:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    db.delete(empresa_banco)
    db.commit()

    return "Empresa deletada com sucesso"

