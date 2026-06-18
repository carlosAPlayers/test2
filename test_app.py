import unittest
from unittest.mock import patch
from io import StringIO

from customer import criar_cliente
from app import main


class TestCriarCliente(unittest.TestCase):
    """Testes para a função criar_cliente."""

    def test_criar_cliente_sucesso(self):
        cliente = criar_cliente("João Silva", "joao@email.com")
        self.assertEqual(cliente["nome"], "João Silva")
        self.assertEqual(cliente["email"], "joao@email.com")

    def test_criar_cliente_strip_espacos(self):
        cliente = criar_cliente("  Maria  ", "  maria@email.com  ")
        self.assertEqual(cliente["nome"], "Maria")
        self.assertEqual(cliente["email"], "maria@email.com")

    def test_criar_cliente_nome_vazio(self):
        with self.assertRaises(ValueError) as ctx:
            criar_cliente("", "joao@email.com")
        self.assertIn("nome", str(ctx.exception))

    def test_criar_cliente_nome_somente_espacos(self):
        with self.assertRaises(ValueError) as ctx:
            criar_cliente("   ", "joao@email.com")
        self.assertIn("nome", str(ctx.exception))

    def test_criar_cliente_email_vazio(self):
        with self.assertRaises(ValueError) as ctx:
            criar_cliente("João", "")
        self.assertIn("e-mail", str(ctx.exception).lower())

    def test_criar_cliente_email_somente_espacos(self):
        with self.assertRaises(ValueError) as ctx:
            criar_cliente("João", "   ")
        self.assertIn("e-mail", str(ctx.exception).lower())

    def test_criar_cliente_nome_none(self):
        with self.assertRaises(ValueError):
            criar_cliente(None, "joao@email.com")

    def test_criar_cliente_email_none(self):
        with self.assertRaises(ValueError):
            criar_cliente("João", None)


class TestAppMain(unittest.TestCase):
    """Testes para o fluxo principal do app."""

    @patch("builtins.input", side_effect=["João Silva", "joao@email.com"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_cadastro_sucesso(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Cliente cadastrado com sucesso", output)

    @patch("builtins.input", side_effect=["", "joao@email.com"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_cadastro_nome_vazio(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Erro", output)

    @patch("builtins.input", side_effect=["João Silva", ""])
    @patch("sys.stdout", new_callable=StringIO)
    def test_cadastro_email_vazio(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Erro", output)

    @patch("builtins.input", side_effect=["", ""])
    @patch("sys.stdout", new_callable=StringIO)
    def test_cadastro_ambos_vazios(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Erro", output)


if __name__ == "__main__":
    unittest.main()
