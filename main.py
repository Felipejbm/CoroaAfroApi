from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session


from database import Base, engine, get_db
from schemas import EmpreendedorCreate, LoginReq
from models import Empreendedor

Base.metadata.create_all(bind=engine) 
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins= [
        "http://localhost:5173"
    ],
    allow_credentials= True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post('/login')
def logar(
    dados: LoginReq,
    db: Session = Depends(get_db)
):
    empreendedor = db.query(Empreendedor).filter(
        Empreendedor.email == dados.email
    ).first()

    if not empreendedor:
        raise HTTPException(
            status_code= 404,
            detail="Empreendedor não encontrado"
        )

    if empreendedor.senha != dados.senha:
        raise HTTPException(
            status_code= 401,
            detail= "Senha incorreta"
        )

    return{
        "Msg": "Login realizado com sucesso!",
        "Empreendedor": {
            "id": empreendedor.id_empreendedor,
            "nome": empreendedor.nome,
            "email": empreendedor.email
        }

    }

@app.post('/criar-empreendedor')
def criar_empreendedor(empreendedor: EmpreendedorCreate, db: Session = Depends(get_db)):
    novo_empreendedor = Empreendedor(
        nome = empreendedor.nome,
        email = empreendedor.email,
        senha = empreendedor.senha,
        telefone = empreendedor.telefone,
    )

    db.add(novo_empreendedor)
    db.commit()
    db.refresh(novo_empreendedor)

    return{
        "Msg": "Empreendedor criado com sucesso!",
        "Empreendedor": novo_empreendedor
    }