#!/usr/bin/env python3
"""
experimentos/demo_melhorias.py — Seção 7 do roteiro: demonstração das melhorias.

Melhorias implementadas em portscanner.py:
    M1 Execução concorrente com limite  (-w)       -> comparada com execução sequencial
    M2 Exportação de resultados         (-o .json/.csv)
    M3 Medição de desempenho            (duração no resumo e em meta.duracao_s; tempo por porta)
    M4 Identificação de serviços        (coluna SERVIÇO*, com aviso de que não confirma nada)
    M5 Interface de linha de comando    (argparse, --help)
    M6 Registro de execução             (--log)

Evidência: evidencias/06_melhorias.md (+ 06_exemplo.json, 06_exemplo.csv, 06_exemplo.log)
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import EVIDENCIAS, RAIZ, SCANNER, cabecalho, salvar  # noqa: E402
from lab.servidor_teste import PortaSaturada, ServicoTCP  # noqa: E402

A = "127.0.0.1"


def rodar(*args: str) -> str:
    p = subprocess.run([sys.executable, str(SCANNER), *args], capture_output=True, text=True)
    # caminhos relativos na evidência (o repositório não deve expor caminhos da máquina)
    return (p.stdout + p.stderr).replace(str(RAIZ) + "/", "")


def duracao(saida: str) -> float:
    return float(saida.split(" portas verificadas em ")[1].split("s")[0])


def main() -> int:
    EVIDENCIAS.mkdir(exist_ok=True)
    # 4 portas que respondem com timeout + 1 "redis" de mentira (6379) para M4
    servicos = []
    try:
        servicos += [PortaSaturada(p).iniciar() for p in (9004, 9005, 9006, 9007)]
        servicos += [ServicoTCP(6379).iniciar(), ServicoTCP(9001).iniciar()]
        portas = "9001,9004-9007,6379"
        seq = rodar(A, "-p", portas, "-t", "1", "-w", "1")
        con = rodar(A, "-p", portas, "-t", "1", "-w", "6",
                    "-o", str(EVIDENCIAS / "06_exemplo.json"), "--log", str(EVIDENCIAS / "06_exemplo.log"))
        rodar(A, "-p", portas, "-t", "1", "-o", str(EVIDENCIAS / "06_exemplo.csv"))
    finally:
        for s in servicos:
            s.parar()

    t_seq, t_con = duracao(seq), duracao(con)
    texto = cabecalho("Melhorias implementadas")
    texto += ("## M1 + M3 — Concorrência com limite e medição de desempenho\n\n"
              "Alvo: 4 portas que não respondem (cada uma custa `-t 1` = 1 s) + 2 abertas.\n\n"
              "| Execução | Parâmetro | Duração total |\n|---|---|---|\n"
              f"| Sequencial | `-w 1` | {t_seq:.2f} s |\n| Concorrente | `-w 6` | {t_con:.2f} s |\n\n"
              f"Ganho observado: ~{t_seq / t_con:.1f}x. O teto de `-w` é 100 para não gerar carga excessiva.\n\n"
              f"Saída da execução concorrente:\n\n```\n{con}```\n\n"
              "## M4 — Identificação de serviços (e por que ela não prova nada)\n\n"
              "A porta 6379 recebeu um serviço de teste que **não é Redis** (só envia um banner de texto); "
              "mesmo assim o scanner exibe o nome `redis`, pois o nome vem da tabela de portas do SO. "
              "Por isso a coluna é marcada com `*` e o rodapé avisa que o nome não confirma o serviço real.\n\n"
              "## M2 — Exportação\n\n`06_exemplo.json` e `06_exemplo.csv` (mesma execução, formatos diferentes).\n\n"
              f"```\n{(EVIDENCIAS / '06_exemplo.csv').read_text(encoding='utf-8')}```\n\n"
              "## M6 — Log de execução\n\n`06_exemplo.log` (cada tentativa e eventuais erros):\n\n"
              f"```\n{(EVIDENCIAS / '06_exemplo.log').read_text(encoding='utf-8')}```\n\n"
              "## M5 — Interface de linha de comando\n\n`python portscanner.py --help`:\n\n"
              f"```\n{rodar('--help')}```\n")
    print(texto[:1200] + "\n[...]")
    print(f"Evidência salva em {salvar('06_melhorias.md', texto)}")
    return 0 if t_con < t_seq else 1


if __name__ == "__main__":
    sys.exit(main())
