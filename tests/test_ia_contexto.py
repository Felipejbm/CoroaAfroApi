import unittest
from datetime import datetime

from services.ia_contexto import _resumir_desempenho


class IaContextoTests(unittest.TestCase):
    def test_calcula_resumo_sem_delegar_matematica_para_ia(self):
        agora = datetime.now().astimezone().isoformat()
        publicacoes = [
            {
                "tipo": "REELS",
                "interacoes_calculadas": 30,
                "taxa_engajamento_seguidores": 3.0,
            },
            {
                "tipo": "IMAGE",
                "interacoes_calculadas": 10,
                "taxa_engajamento_seguidores": 1.0,
            },
        ]
        resumo = _resumir_desempenho(
            {"followers_count": 1000},
            [{"timestamp": agora}, {"timestamp": agora}],
            publicacoes,
            [{"valor": 12}, {"valor": 18}],
        )

        self.assertEqual(resumo["media_interacoes"], 20)
        self.assertEqual(resumo["taxa_engajamento_media_seguidores"], 2)
        self.assertEqual(resumo["melhor_formato_na_amostra"], "REELS")
        self.assertEqual(resumo["publicacoes_ultimos_30_dias"], 2)
        self.assertEqual(resumo["alcance_medio_diario_periodo_disponivel"], 15)

    def test_funciona_sem_publicacoes_ou_seguidores(self):
        resumo = _resumir_desempenho({}, [], [], [])
        self.assertIsNone(resumo["media_interacoes"])
        self.assertIsNone(resumo["taxa_engajamento_media_seguidores"])
        self.assertIsNone(resumo["melhor_formato_na_amostra"])
        self.assertEqual(resumo["frequencia_semanal_aproximada"], 0)


if __name__ == "__main__":
    unittest.main()
