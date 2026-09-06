import hashlib
import json
from dataclasses import dataclass

import httpx
from fastapi import Depends

from config import Settings, get_settings
from services.ia_modos import instrucao_do_modo


class IaServiceError(Exception):
    def __init__(self, mensagem: str, status_code: int = 502):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code


@dataclass(frozen=True)
class IaResultado:
    texto: str
    tokens_entrada: int | None = None
    tokens_saida: int | None = None


class IaService:
    URL = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not settings.openai_api_key:
            raise IaServiceError("A inteligência artificial ainda não foi configurada.", 503)
        self.settings = settings
        self.transport = transport

    async def gerar_resposta(
        self,
        id_empreendedor: int,
        contexto: dict,
        historico: list[dict[str, str]],
        pergunta: str,
        modo: str = "geral",
    ) -> IaResultado:
        mensagens = [
            {"role": item["role"], "content": item["content"]}
            for item in historico[-12:]
        ]
        mensagens.append({"role": "user", "content": pergunta})

        payload = {
            "model": self.settings.openai_model,
            "instructions": self._instrucoes(contexto, modo),
            "input": mensagens,
            "max_output_tokens": self.settings.openai_max_output_tokens,
            "reasoning": {"effort": "minimal"},
            "text": {"verbosity": "low"},
            "store": False,
            "safety_identifier": hashlib.sha256(
                f"coroa:{id_empreendedor}".encode("utf-8")
            ).hexdigest(),
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.openai_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(self.URL, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise IaServiceError("A IA demorou para responder. Tente novamente.", 504) from exc
        except httpx.HTTPError as exc:
            raise IaServiceError("Não foi possível acessar a IA agora.", 503) from exc

        if response.status_code == 429:
            raise IaServiceError("Limite temporário da IA atingido. Aguarde um pouco.", 429)
        if response.status_code in {401, 403}:
            raise IaServiceError("A configuração da IA precisa ser revisada.", 503)
        if response.is_error:
            raise IaServiceError("A IA não conseguiu gerar uma resposta.", 502)

        dados = response.json()
        if dados.get("status") == "incomplete":
            motivo = (dados.get("incomplete_details") or {}).get("reason")
            if motivo == "max_output_tokens":
                raise IaServiceError(
                    "A IA atingiu o limite da resposta antes de terminar. Tente uma pergunta mais curta.",
                    502,
                )
            raise IaServiceError("A IA não conseguiu concluir a resposta.", 502)
        texto = self._extrair_texto(dados)
        uso = dados.get("usage") or {}
        return IaResultado(
            texto=texto,
            tokens_entrada=uso.get("input_tokens"),
            tokens_saida=uso.get("output_tokens"),
        )

    @staticmethod
    def _extrair_texto(dados: dict) -> str:
        texto_direto = dados.get("output_text")
        if isinstance(texto_direto, str) and texto_direto.strip():
            return texto_direto.strip()

        partes = []
        for item in dados.get("output", []):
            if item.get("type") != "message":
                continue
            for conteudo in item.get("content", []):
                if conteudo.get("type") == "output_text" and conteudo.get("text"):
                    partes.append(conteudo["text"])
        texto = "\n".join(partes).strip()
        if not texto:
            raise IaServiceError("A IA retornou uma resposta vazia.", 502)
        return texto

    @staticmethod
    def _instrucoes(contexto: dict, modo: str) -> str:
        contexto_json = json.dumps(contexto, ensure_ascii=False, default=str)
        return (
            "Papel: você é a assistente de negócios do Coroa Afro, uma plataforma de apoio a "
            "pequenos empreendedores, especialmente empreendedores negros. "
            "Personalidade: acolhedora, respeitosa, encorajadora, direta e sem julgamento. "
            "Objetivo: transformar a dúvida do empreendedor em entendimento e próximos passos "
            "realistas, acessíveis e adequados aos recursos de uma pequena empresa. "
            "Responda em português brasileiro e explique termos técnicos quando precisar usá-los. "
            "Diferencie claramente fatos presentes nos dados, interpretações e sugestões. "
            "Use somente os dados fornecidos no contexto; não invente métricas, resultados, "
            "produtos, preços, público-alvo ou informações sobre a empresa. "
            "Quando faltar uma informação importante, diga exatamente o que falta e ainda ofereça "
            "uma orientação geral útil. Prefira de três a cinco passos curtos e priorizados. "
            "Não peça nem revele senhas, tokens, CPF, telefone ou credenciais. "
            "Não substitua orientação profissional jurídica, médica ou financeira. "
            f"Tarefa especializada selecionada: {instrucao_do_modo(modo)} "
            f"Contexto seguro do empreendedor: {contexto_json}"
        )


def get_ia_service(settings: Settings = Depends(get_settings)) -> IaService:
    return IaService(settings)
