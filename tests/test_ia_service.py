import asyncio
import json
import unittest

import httpx
from pydantic import SecretStr

from config import Settings
from services.ia_service import IaService, IaServiceError


class IaServiceTests(unittest.TestCase):
    def test_monta_requisicao_segura_e_interpreta_resposta(self):
        requisicoes = []

        def responder(request: httpx.Request):
            requisicoes.append(request)
            return httpx.Response(200, json={
                "output": [{
                    "type": "message",
                    "content": [{"type": "output_text", "text": "Plano pronto."}],
                }],
                "usage": {"input_tokens": 20, "output_tokens": 4},
            })

        settings = Settings(
            database_url="sqlite://",
            openai_api_key=SecretStr("chave-de-teste"),
            openai_model="gpt-5",
        )
        service = IaService(settings, transport=httpx.MockTransport(responder))
        resultado = asyncio.run(service.gerar_resposta(
            id_empreendedor=7,
            contexto={"empresa": {"segmento": "alimentacao"}},
            historico=[{"role": "assistant", "content": "Olá!"}],
            pergunta="Crie um plano.",
        ))

        self.assertEqual(resultado.texto, "Plano pronto.")
        self.assertEqual(resultado.tokens_entrada, 20)
        payload = json.loads(requisicoes[0].content)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["reasoning"]["effort"], "minimal")
        self.assertEqual(payload["text"]["verbosity"], "low")
        self.assertIn("assistente de negócios do Coroa Afro", payload["instructions"])
        self.assertIn("fatos presentes nos dados", payload["instructions"])
        self.assertEqual(payload["input"][-1]["content"], "Crie um plano.")
        self.assertNotIn("chave-de-teste", requisicoes[0].content.decode())
        self.assertEqual(
            requisicoes[0].headers["Authorization"],
            "Bearer chave-de-teste",
        )

    def test_rejeita_resposta_vazia(self):
        settings = Settings(
            database_url="sqlite://",
            openai_api_key=SecretStr("teste"),
        )
        service = IaService(
            settings,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"output": []})
            ),
        )
        with self.assertRaises(IaServiceError):
            asyncio.run(service.gerar_resposta(1, {}, [], "Olá"))

    def test_explica_resposta_interrompida_por_limite(self):
        settings = Settings(
            database_url="sqlite://",
            openai_api_key=SecretStr("teste"),
        )
        service = IaService(
            settings,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
            })),
        )
        with self.assertRaisesRegex(IaServiceError, "atingiu o limite"):
            asyncio.run(service.gerar_resposta(1, {}, [], "Olá"))


if __name__ == "__main__":
    unittest.main()
