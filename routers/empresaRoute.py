from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Empresa
from schemas import EmpresaCreate

router = APIRouter(
    prefix="/empresa",
    tags=["Empresa"]
)

@router.post('/criar-empresa')
def criar_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    nova_empresa = Empresa(
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