"""
Testes automatizados do scanner (apenas loopback; nada sai da máquina).

Rodar, a partir da raiz do projeto:
    python -m unittest discover -s tests -v
"""

import errno
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import portscanner as ps                                   # noqa: E402
from lab.servidor_teste import PortaSaturada, ServicoTCP   # noqa: E402


def porta_livre() -> int:
    """Pede ao SO uma porta efêmera livre (e a devolve)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestParsePortas(unittest.TestCase):
    def test_validas(self):
        self.assertEqual(ps.parse_portas("80"), [80])
        self.assertEqual(ps.parse_portas("20-23"), [20, 21, 22, 23])
        self.assertEqual(ps.parse_portas("443, 22,80"), [22, 80, 443])
        self.assertEqual(ps.parse_portas("1-3,2-4"), [1, 2, 3, 4])          # sem repetição
        self.assertEqual(ps.parse_portas("65535"), [65535])

    def test_invalidas(self):
        for texto in ["", "   ", "0", "65536", "70000", "abc", "-5", "1-2-3", "100-50",
                      "80,,443", "80,", "1.5", "²"]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    ps.parse_portas(texto)


class TestResolverAlvo(unittest.TestCase):
    def test_ip_valido(self):
        self.assertEqual(ps.resolver_alvo("127.0.0.1"), (socket.AF_INET, "127.0.0.1"))

    def test_invalido(self):
        for alvo in ["", "  ", "alvo.invalid", "999.999.999.999"]:
            with self.subTest(alvo=alvo):
                with self.assertRaises(ValueError):
                    ps.resolver_alvo(alvo)

    def test_alvo_nao_publico(self):
        self.assertTrue(ps.alvo_nao_publico("127.0.0.1"))
        self.assertTrue(ps.alvo_nao_publico("192.168.0.5"))
        self.assertTrue(ps.alvo_nao_publico("::1"))
        self.assertFalse(ps.alvo_nao_publico("8.8.8.8"))


class TestTentativaDeConexao(unittest.TestCase):
    def test_aberta(self):
        porta = porta_livre()
        s = ServicoTCP(porta).iniciar()
        try:
            r = ps.verificar_porta("127.0.0.1", socket.AF_INET, "127.0.0.1", porta, 1)
            self.assertEqual(r.estado, ps.ABERTA)
        finally:
            s.parar()

    def test_fechada(self):
        r = ps.verificar_porta("127.0.0.1", socket.AF_INET, "127.0.0.1", porta_livre(), 1)
        self.assertEqual(r.estado, ps.FECHADA)

    def test_timeout(self):
        porta = porta_livre()
        s = PortaSaturada(porta).iniciar()
        try:
            r = ps.verificar_porta("127.0.0.1", socket.AF_INET, "127.0.0.1", porta, 0.4)
            self.assertEqual(r.estado, ps.TIMEOUT)
            self.assertGreaterEqual(r.tempo_ms, 350)       # esperou de fato o tempo limite
        finally:
            s.parar()

    def test_outro_erro_de_comunicacao(self):
        """Simula 'rede inalcançável' para garantir que cai em ERRO (e não em FECHADA/TIMEOUT)."""
        falso = mock.MagicMock()
        falso.__enter__.return_value.connect.side_effect = OSError(errno.ENETUNREACH, "Network is unreachable")
        with mock.patch("portscanner.socket.socket", return_value=falso):
            r = ps.verificar_porta("x", socket.AF_INET, "10.0.0.1", 80, 1)
        self.assertEqual(r.estado, ps.ERRO)
        self.assertIn("ENETUNREACH", r.detalhe)

    def test_excecao_inesperada_nao_propaga(self):
        with mock.patch("portscanner.tentar_conexao", side_effect=RuntimeError("boom")):
            r = ps.verificar_porta("x", socket.AF_INET, "127.0.0.1", 80, 1)
        self.assertEqual(r.estado, ps.ERRO)

    def test_socket_e_sempre_fechado(self):
        falso = mock.MagicMock()
        with mock.patch("portscanner.socket.socket", return_value=falso):
            ps.tentar_conexao(socket.AF_INET, "127.0.0.1", 80, 1)
        falso.__exit__.assert_called_once()                 # 'with' -> close() garantido


class TestEscanear(unittest.TestCase):
    def test_falha_em_uma_porta_nao_impede_as_demais(self):
        ab, fe = porta_livre(), porta_livre()
        s = ServicoTCP(ab).iniciar()
        original = ps.tentar_conexao

        def instavel(familia, ip, porta, timeout):
            if porta == fe:
                raise RuntimeError("falha simulada")
            return original(familia, ip, porta, timeout)

        try:
            res: list = []
            with mock.patch("portscanner.tentar_conexao", instavel):
                ps.escanear("127.0.0.1", socket.AF_INET, "127.0.0.1", sorted([ab, fe]), 1, 4, res)
        finally:
            s.parar()
        estados = {r.porta: r.estado for r in res}
        self.assertEqual(estados[ab], ps.ABERTA)
        self.assertEqual(estados[fe], ps.ERRO)

    def test_concorrencia_respeita_limite(self):
        import threading
        ativas, pico, lock = 0, 0, threading.Lock()

        def lenta(familia, ip, porta, timeout):
            nonlocal ativas, pico
            with lock:
                ativas += 1
                pico = max(pico, ativas)
            threading.Event().wait(0.05)
            with lock:
                ativas -= 1
            return ps.FECHADA, "x"

        res: list = []
        with mock.patch("portscanner.tentar_conexao", lenta):
            ps.escanear("h", socket.AF_INET, "127.0.0.1", list(range(1, 41)), 1, 5, res)
        self.assertEqual(len(res), 40)
        self.assertLessEqual(pico, 5)


class TestCLI(unittest.TestCase):
    def test_codigos_de_saida(self):
        with mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            with self.assertRaises(SystemExit) as c:
                ps.main(["127.0.0.1", "-p", "70000"])
            self.assertEqual(c.exception.code, 2)
            self.assertEqual(ps.main(["alvo.invalid", "-p", "80"]), 2)
            self.assertEqual(ps.main(["8.8.8.8", "-p", "53"]), 2)      # público sem --autorizado

    def test_exportacao_json_e_csv(self):
        import csv, json, tempfile
        porta = porta_livre()
        s = ServicoTCP(porta).iniciar()
        try:
            with tempfile.TemporaryDirectory() as d, mock.patch("sys.stdout"):
                j, c = Path(d, "r.json"), Path(d, "r.csv")
                self.assertEqual(ps.main(["127.0.0.1", "-p", str(porta), "-o", str(j)]), 0)
                self.assertEqual(ps.main(["127.0.0.1", "-p", str(porta), "-o", str(c)]), 0)
                dados = json.loads(j.read_text())
                self.assertEqual(dados["resultados"][0]["estado"], "ABERTA")
                self.assertIn("duracao_s", dados["meta"])
                with c.open(newline="") as f:
                    linhas = list(csv.DictReader(f))
                self.assertEqual(linhas[0]["estado"], "ABERTA")
        finally:
            s.parar()


if __name__ == "__main__":
    unittest.main()
