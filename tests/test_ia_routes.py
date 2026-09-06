import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from dependencies import get_current_user
from models import EmpreendedorDB, IaMensagemDB
from routers.iaRoute import router
from services.ia_service import IaResultado, get_ia_service


class IaFalsa:
    def __init__(self):
        self.chamadas = []

    async def gerar_resposta(self, **dados):
        self.chamadas.append(dados)
        return IaResultado(
            texto="Analise seu alcance semanal e teste dois formatos de conteúdo.",
            tokens_entrada=25,
            tokens_saida=12,
        )


class IaRoutesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        with self.Session() as db:
            db.add_all([
                EmpreendedorDB(nome="Pessoa 1", email="p1@example.com", senha="x", telefone="1"),
                EmpreendedorDB(nome="Pessoa 2", email="p2@example.com", senha="x", telefone="2"),
            ])
            db.commit()

        self.usuario_atual = 1
        app = FastAPI()
        app.include_router(router)

        def banco_teste():
            with self.Session() as db:
                yield db

        def usuario_teste():
            with self.Session() as db:
                return db.get(EmpreendedorDB, self.usuario_atual)

        app.dependency_overrides[get_db] = banco_teste
        app.dependency_overrides[get_current_user] = usuario_teste
        self.ia_falsa = IaFalsa()
        app.dependency_overrides[get_ia_service] = lambda: self.ia_falsa
        self.client = TestClient(app)

    def tearDown(self):
        self.engine.dispose()

    def test_fluxo_completo_da_conversa(self):
        criada = self.client.post("/ia/conversas", json={"titulo": "Plano de conteúdo"})
        self.assertEqual(criada.status_code, 201)
        id_conversa = criada.json()["id_conversa"]

        resposta = self.client.post(
            f"/ia/conversas/{id_conversa}/mensagens",
            json={"conteudo": "Como melhorar meu alcance?"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["mensagem_usuario"]["papel"], "usuario")
        self.assertEqual(resposta.json()["mensagem_assistente"]["papel"], "assistente")
        self.assertEqual(len(self.ia_falsa.chamadas), 1)
        self.assertEqual(
            self.ia_falsa.chamadas[0]["pergunta"],
            "Como melhorar meu alcance?",
        )
        contexto = self.ia_falsa.chamadas[0]["contexto"]
        self.assertEqual(contexto["empreendedor"]["primeiro_nome"], "Pessoa")
        self.assertEqual(contexto["metas_ativas"], [])
        self.assertEqual(contexto["trilhas_em_andamento"], [])
        self.assertFalse(contexto["instagram"]["conectado"])
        self.assertEqual(self.ia_falsa.chamadas[0]["modo"], "geral")
        with self.Session() as db:
            mensagem_ia = db.query(IaMensagemDB).filter(
                IaMensagemDB.papel == "assistente"
            ).one()
            self.assertEqual(mensagem_ia.tokens_entrada, 25)
            self.assertEqual(mensagem_ia.tokens_saida, 12)

    def test_lista_modos_e_valida_escolha(self):
        modos = self.client.get("/ia/modos")
        self.assertEqual(modos.status_code, 200)
        ids = {item["id"] for item in modos.json()}
        self.assertIn("analisar_instagram", ids)
        self.assertIn("calendario_conteudo", ids)

        id_conversa = self.client.post("/ia/conversas", json={}).json()["id_conversa"]
        resposta = self.client.post(
            f"/ia/conversas/{id_conversa}/mensagens",
            json={"conteudo": "Analise meu perfil", "modo": "analisar_instagram"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.ia_falsa.chamadas[-1]["modo"], "analisar_instagram")

        invalida = self.client.post(
            f"/ia/conversas/{id_conversa}/mensagens",
            json={"conteudo": "Teste", "modo": "modo_inexistente"},
        )
        self.assertEqual(invalida.status_code, 422)

        mensagens = self.client.get(f"/ia/conversas/{id_conversa}/mensagens")
        self.assertEqual([item["papel"] for item in mensagens.json()], ["usuario", "assistente"])

    def test_usuario_nao_acessa_conversa_de_outro(self):
        id_conversa = self.client.post("/ia/conversas", json={}).json()["id_conversa"]
        self.usuario_atual = 2
        resposta = self.client.get(f"/ia/conversas/{id_conversa}/mensagens")
        self.assertEqual(resposta.status_code, 404)

    def test_conversa_arquivada_nao_recebe_mensagem(self):
        id_conversa = self.client.post("/ia/conversas", json={}).json()["id_conversa"]
        self.assertEqual(
            self.client.patch(f"/ia/conversas/{id_conversa}/arquivar").status_code,
            204,
        )
        resposta = self.client.post(
            f"/ia/conversas/{id_conversa}/mensagens",
            json={"conteudo": "Teste"},
        )
        self.assertEqual(resposta.status_code, 409)


if __name__ == "__main__":
    unittest.main()
