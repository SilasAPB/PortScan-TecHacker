#!/usr/bin/env python3
"""
experimentos/tratamento_erros.py — Seção 4 do roteiro: tratamento de erros.

Exercita, de ponta a ponta (pela linha de comando), as 7 situações exigidas:
    1 porta com serviço ativo   2 porta sem serviço     3 número de porta inválido
    4 intervalo inválido        5 endereço inválido     6 timeout de conexão
    7 interrupção pelo usuário (Ctrl+C = SIGINT de verdade)

Para cada uma registra comando, código de saída e saída. Evidência: 05_tratamento_erros.md.
Critério de sucesso: nenhuma situação pode terminar com "Traceback" (encerramento inesperado).
"""

import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import SCANNER, cabecalho, salvar          # noqa: E402
from lab.servidor_teste import PortaSaturada, ServicoTCP  # noqa: E402

A = "127.0.0.1"
# (situação, argumentos, código de saída esperado)
CASOS = [
    ("1. Porta com serviço ativo", [A, "-p", "9001"], 0),
    ("2. Porta sem serviço", [A, "-p", "9003"], 0),
    ("3a. Porta inválida (acima de 65535)", [A, "-p", "70000"], 2),
    ("3b. Porta inválida (texto)", [A, "-p", "http"], 2),
    ("3c. Porta inválida (zero)", [A, "-p", "0"], 2),
    ("4a. Intervalo invertido", [A, "-p", "100-50"], 2),
    ("4b. Intervalo malformado", [A, "-p", "1-2-3"], 2),
    ("5. Endereço de destino inválido", ["alvo.invalid", "-p", "80"], 2),
    ("5b. Endereço público sem autorização", ["8.8.8.8", "-p", "53"], 2),
    ("6. Timeout de conexão", [A, "-p", "9004", "-t", "0.5"], 0),
    ("6b. Timeout inválido", [A, "-p", "80", "-t", "0"], 2),
]


def executar(args: list[str]) -> tuple[str, int]:
    p = subprocess.run([sys.executable, str(SCANNER), *args], capture_output=True, text=True, timeout=60)
    return (p.stdout + p.stderr).strip(), p.returncode


def ctrl_c() -> tuple[str, int]:
    """Inicia um scan lento (sequencial, porta que dá timeout em 5 s) e envia SIGINT após 1 s."""
    p = subprocess.Popen([sys.executable, str(SCANNER), A, "-p", "9003,9004,9005-9010",
                          "-t", "5", "-w", "1"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(1.0)
    p.send_signal(signal.SIGINT)
    saida, _ = p.communicate(timeout=30)
    return saida.strip(), p.returncode


def main() -> int:
    servicos = [ServicoTCP(9001).iniciar(), PortaSaturada(9004).iniciar()]
    texto = cabecalho("Tratamento de erros — as 7 situações do roteiro")
    falhas = 0
    try:
        casos = [(s, ["python portscanner.py", *a], *executar(a), esp) for s, a, esp in CASOS]
        saida, cod = ctrl_c()
        casos.append(("7. Interrupção pelo usuário (Ctrl+C / SIGINT)",
                      ["python portscanner.py", A, "-p 9003,9004,9005-9010 -t 5 -w 1  # + SIGINT após 1 s"],
                      saida, cod, 130))
    finally:
        for s in servicos:
            s.parar()

    texto += "| Situação | Código de saída (esperado) | Sem Traceback? |\n|---|---|---|\n"
    detalhes = ""
    for situacao, cmd, saida, cod, esperado in casos:
        sem_traceback = "Traceback" not in saida
        ok = sem_traceback and cod == esperado
        falhas += not ok
        texto += f"| {situacao} | {cod} ({esperado}) | {'sim' if sem_traceback else 'NÃO'} |\n"
        detalhes += f"\n## {situacao}\n\n`{' '.join(cmd)}` → código de saída **{cod}**\n\n```\n{saida}\n```\n"
    texto += ("\nCódigos: 0 = execução normal | 2 = parâmetro inválido | 130 = interrompido (Ctrl+C).\n" + detalhes)
    caminho = salvar("05_tratamento_erros.md", texto)
    print(texto.split("\n## ")[0])
    print(f"Evidência salva em {caminho}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
