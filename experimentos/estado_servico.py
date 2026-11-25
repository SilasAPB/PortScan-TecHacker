#!/usr/bin/env python3
"""
experimentos/estado_servico.py — Seção 6 do roteiro: mudanças no estado do serviço.

    Rodada A: serviço ATIVO       -> scanner -> esperado ABERTA
    Rodada B: serviço INTERROMPIDO -> scanner -> esperado FECHADA
    Rodada C: serviço REINICIADO  -> scanner -> esperado ABERTA

Em cada rodada, `ss -ltn` (ferramenta do SO) confirma se a porta está mesmo em LISTEN,
independente do scanner. Resultado em evidencias/03_experimento_estado.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import cabecalho, comando, rodar_scanner, salvar  # noqa: E402
from lab.servidor_teste import ServicoTCP                    # noqa: E402

ALVO, PORTA = "127.0.0.1", 9001


def rodada(nome: str, esperado: str) -> dict:
    ss = comando("ss", "-ltn", f"sport = :{PORTA}")
    saida, res, _ = rodar_scanner(ALVO, "-p", str(PORTA), "-t", "1")
    r = res[PORTA]
    return {"nome": nome, "esperado": esperado, "estado": r["estado"],
            "tempo": r["tempo_ms"], "detalhe": r["detalhe"], "ss": ss, "saida": saida}


def main() -> int:
    rodadas = []
    servico = ServicoTCP(PORTA, ALVO).iniciar()
    rodadas.append(rodada("A — serviço ativo", "ABERTA"))
    servico.parar()
    rodadas.append(rodada("B — serviço interrompido", "FECHADA"))
    servico = ServicoTCP(PORTA, ALVO).iniciar()
    rodadas.append(rodada("C — serviço reiniciado", "ABERTA"))
    servico.parar()

    texto = cabecalho("Experimento de mudança de estado do serviço") + f"Porta testada: {ALVO}:{PORTA}\n\n"
    texto += "| Rodada | Esperado | Scanner | Tempo (ms) | Confere? |\n|---|---|---|---|---|\n"
    for r in rodadas:
        texto += f"| {r['nome']} | {r['esperado']} | {r['estado']} | {r['tempo']} | {'sim' if r['esperado'] == r['estado'] else 'NÃO'} |\n"
    for r in rodadas:
        texto += (f"\n## Rodada {r['nome']}\n\n"
                  f"Verificação independente do SO — `ss -ltn \"sport = :{PORTA}\"`:\n\n```\n{r['ss']}\n```\n\n"
                  f"Saída do scanner:\n\n```\n{r['saida']}```\n")
    caminho = salvar("03_experimento_estado.md", texto)
    print(texto.split("\n## ")[0])
    print(f"Evidência salva em {caminho}")
    return 0 if all(r["esperado"] == r["estado"] for r in rodadas) else 1


if __name__ == "__main__":
    sys.exit(main())
