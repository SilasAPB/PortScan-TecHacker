#!/usr/bin/env python3
"""
experimentos/efeito_timeout.py — Seção 4/8 do roteiro: por que TIMEOUT != porta fechada.

Cenário 1 — porta saturada que NUNCA responde (equivale a firewall com DROP):
    qualquer timeout resulta em TIMEOUT; aumentar o tempo só atrasa o resultado.

Cenário 2 — porta "lenta": começa saturada, mas o serviço volta a atender 0,4 s depois.
    A porta ESTÁ aberta, porém o primeiro SYN foi descartado e o cliente só retransmite
    após ~1 s (RTO inicial do TCP):
        timeout 0,5 s -> TIMEOUT  (conclusão errada se interpretado como "fechada")
        timeout 3,0 s -> ABERTA   (mesma porta, mesmo instante, outro timeout)

Resultado em evidencias/04_efeito_timeout.md.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import cabecalho, rodar_scanner, salvar  # noqa: E402
from lab.servidor_teste import PortaSaturada        # noqa: E402

ALVO, PORTA = "127.0.0.1", 9004


def cenario(liberar_apos: float | None, timeout: str) -> dict:
    porta = PortaSaturada(PORTA, ALVO).iniciar()
    if liberar_apos is not None:
        threading.Timer(liberar_apos, porta.liberar).start()
    try:
        _, res, _ = rodar_scanner(ALVO, "-p", str(PORTA), "-t", timeout)
    finally:
        threading.Event().wait((liberar_apos or 0) + 0.1)   # garante que o Timer já disparou
        porta.parar()
    return res[PORTA]


def main() -> int:
    casos = [
        ("1. Nunca responde (DROP)", None, "0.5"),
        ("1. Nunca responde (DROP)", None, "3"),
        ("2. Serviço volta após 0,4 s", 0.4, "0.5"),
        ("2. Serviço volta após 0,4 s", 0.4, "3"),
    ]
    texto = cabecalho("Efeito do tempo limite (timeout) no resultado")
    texto += "| Cenário | Timeout (-t) | Resultado | Tempo (ms) | A porta estava realmente... |\n|---|---|---|---|---|\n"
    saidas = []
    for nome, libera, t in casos:
        r = cenario(libera, t)
        real = "inacessível" if libera is None else "ABERTA (serviço voltou)"
        texto += f"| {nome} | {t} s | {r['estado']} | {r['tempo_ms']} | {real} |\n"
        saidas.append((nome, t, r))
    texto += ("\nLeitura: no cenário 2 a mesma porta aparece como TIMEOUT com `-t 0.5` e como ABERTA com `-t 3`. "
              "Logo, TIMEOUT só informa que não houve resposta *dentro do tempo escolhido*.\n")
    caminho = salvar("04_efeito_timeout.md", texto)
    print(texto)
    print(f"Evidência salva em {caminho}")
    # sucesso do experimento = comportamento esperado observado
    esperado = ["TIMEOUT", "TIMEOUT", "TIMEOUT", "ABERTA"]
    return 0 if [r["estado"] for _, _, r in saidas] == esperado else 1


if __name__ == "__main__":
    sys.exit(main())
