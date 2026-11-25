#!/usr/bin/env python3
"""
experimentos/testes_iniciais.py — Seção 3.3 do roteiro: testes iniciais.

Sobe serviços de teste, escaneia portas com e sem serviço e confronta o resultado com
`ss -ltn` (ferramenta do SO que lista portas em estado LISTEN).
Evidência: evidencias/01_testes_iniciais.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import cabecalho, comando, rodar_scanner, salvar  # noqa: E402
from lab.servidor_teste import PortaSaturada, ServicoTCP     # noqa: E402


def main() -> int:
    servicos = [ServicoTCP(9001).iniciar(), ServicoTCP(9002).iniciar(), PortaSaturada(9004).iniciar()]
    try:
        ss = comando("ss", "-ltn")
        saida, res, _ = rodar_scanner("127.0.0.1", "-p", "9001-9005", "-t", "1")
    finally:
        for s in servicos:
            s.parar()

    linhas_ss = "\n".join(l for l in ss.splitlines() if l.startswith("State") or ":900" in l)
    texto = cabecalho("Testes iniciais")
    texto += ("Montagem: serviços ativos em 9001 e 9002; 9004 saturada (sem resposta); 9003 e 9005 sem nada escutando.\n\n"
              "## Verificação pelo sistema operacional — `ss -ltn` (somente linhas relevantes)\n\n"
              f"```\n{linhas_ss}\n```\n\n"
              "Observação: 9001, 9002 e 9004 aparecem em LISTEN; 9003 e 9005 não aparecem.\n\n"
              "## Saída do scanner — `python portscanner.py 127.0.0.1 -p 9001-9005 -t 1`\n\n"
              f"```\n{saida}```\n")
    esperado = {9001: "ABERTA", 9002: "ABERTA", 9003: "FECHADA", 9004: "TIMEOUT", 9005: "FECHADA"}
    ok = all(res[p]["estado"] == e for p, e in esperado.items())
    texto += f"\nTodas as portas conferem com o esperado: **{'sim' if ok else 'NÃO'}**.\n"
    print(salvar("01_testes_iniciais.md", texto).read_text(encoding="utf-8"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
