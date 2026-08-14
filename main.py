from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db

from schemas import (
    EmpreendedorCreate, 
    LoginReq, 
    TrilhaCreate, 
    AtividadeCreate,
    MensagemChatCreate,
    MentorCreate, 
    PostagemChatCreate,
    TransacoesCreate,
    SaldoCreate,
    MetricasMarketingCreate,
    EmpresaCreate
)
from models import (
    Empreendedor, 
    Trilha, 
    Atividade, 
    MensagemChat, 
    Mentor, 
    PostagemChat,
    Transacao,
    Saldo,
    MetricasMarketing,
    Empresa
)

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

@app.post('/criar-empresa')
def criar_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    nova_empresa = Empresa(
        nome = empresa.nome,
        data_fundacao = empresa.data_fundacao,
        cnpj = empresa.cnpj,
        segmento = empresa.segmento,
        endereco = empresa.endereco,
        porte = empresa.porte,
        num_funcionarios = empresa.num_funcionarios
    )

    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)

    return{
        "Msg": "Empresa criada com sucesso!",
        "Empresa": nova_empresa

    }  
  
@app.post('/criar-trilha')
def criar_trilha(trilha: TrilhaCreate, db: Session = Depends(get_db)):
    nova_trilha = Trilha(
        titulo = trilha.titulo,
        tipo_trilha = trilha.tipo_trilha
    )

    db.add(nova_trilha)
    db.commit()
    db.refresh(nova_trilha)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_trilha
    }

@app.post('/criar-atividade')
def criar_atividade(atividade: AtividadeCreate, db: Session = Depends(get_db)):
    nova_atividade = Atividade(
        titulo_tarefa = atividade.titulo_tarefa,
        conteudo = atividade.conteudo
    )

    db.add(nova_atividade)
    db.commit()
    db.refresh(nova_atividade)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_atividade
    }

@app.post('/criar-mentor')
def criar_mentor(mentor: MentorCreate, db: Session = Depends(get_db)):
    novo_mentor = Mentor(
        nome = mentor.nome,
        especialidade = mentor.especialidade,
        biografia = mentor.biografia
    )

    db.add(novo_mentor)
    db.commit()
    db.refresh(novo_mentor)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": novo_mentor
    }

@app.post('/criar-mensagem')
def criar_mensagem(mensagem: MensagemChatCreate, db: Session = Depends(get_db)):
    nova_mensagem = MensagemChat(
        texto_mensagem = mensagem.texto_mensagem,
        data_envio = mensagem.data_envio,
        lida = mensagem.lida
    )

    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_mensagem
    }

@app.post('/criar-postagem')
def criar_postagem(postagem: PostagemChatCreate, db: Session = Depends(get_db)):
    nova_postagem = PostagemChat(
       conteudo_texto = postagem.conteudo_texto,
       midia_url = postagem.midia_url,
       data_publicacao = postagem.data_publicacao
    )

    db.add(nova_postagem)
    db.commit()
    db.refresh(nova_postagem)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_postagem
    }

@app.post('/adicionar-transacao')
def adicionar_trasacao(transacao: TransacoesCreate, db: Session = Depends(get_db)):
    nova_transacao = Transacao(
        valor = transacao.valor,
        data = transacao.data,
        status = transacao.status
    )

    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": nova_transacao
    }

@app.post('/adicionar-saldo')
def adicionar_saldo(saldo: SaldoCreate, db: Session = Depends(get_db)):
    novo_saldo = Saldo(
        saldo = saldo.saldo,
        meta_faturamento = saldo.meta_faturamento,
        data = saldo.data,
        total_entradas = saldo.total_entradas,
        total_saidas = saldo.total_saidas,
        valor_inicial = saldo.valor_inicial,
        valor_final =  saldo.saldo_final
    )

    db.add(novo_saldo)
    db.commit()
    db.refresh(novo_saldo)

    return{
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": novo_saldo
    }

@app.post('/buscar-metricas-marketing')
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
        "Msg": "Trilha criada com sucesso!",
        "Empreendedor": novas_metricas
    }


