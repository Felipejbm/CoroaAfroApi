import unittest

from pydantic import ValidationError
from sqlalchemy import create_engine, inspect

from database import Base
from schemas.IaSchema.IaSchema import IaConversaCriar, IaMensagemCriar

# Importar models registra as tabelas no metadata do SQLAlchemy.
import models  # noqa: F401, E402


class IaModelsTests(unittest.TestCase):
    def test_tabelas_da_ia_sao_criadas(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        tabelas = set(inspect(engine).get_table_names())
        self.assertIn("ia_conversa", tabelas)
        self.assertIn("ia_mensagem", tabelas)

    def test_schema_limpa_texto(self):
        self.assertEqual(IaConversaCriar(titulo="  Planejamento  ").titulo, "Planejamento")
        self.assertEqual(IaMensagemCriar(conteudo="  Como crescer?  ").conteudo, "Como crescer?")

    def test_schema_rejeita_mensagem_invalida(self):
        with self.assertRaises(ValidationError):
            IaMensagemCriar(conteudo="   ")
        with self.assertRaises(ValidationError):
            IaMensagemCriar(conteudo="x" * 4001)


if __name__ == "__main__":
    unittest.main()
