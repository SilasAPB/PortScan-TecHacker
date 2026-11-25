#!/usr/bin/env python3
"""
experimentos/comparar_nmap.py — Seção 5 do roteiro: validação com Nmap (-sT).

Sobe o laboratório local, roda o scanner próprio E o `nmap -sT` contra as MESMAS portas
e monta a tabela comparativa em evidencias/02_comparacao_nmap.md.

O Nmap é executado aqui apenas como ferramenta de VALIDAÇÃO (permitido pelo roteiro);
o portscanner.py nunca o chama.

Pré-requisito: nmap instalado (sudo apt install nmap). Sem ele, o script ainda roda o
scanner próprio e marca a coluna do Nmap como "N/D" — nunca inventa resultado.
"""

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import EVIDENCIAS, RAIZ, cabecalho, rodar_scanner, salvar  # noqa: E402
from lab.servidor_teste import PortaSaturada, ServicoTCP        # noqa: E402

ALVO = "127.0.0.1"
TIMEOUT = "1"
# porta -> estado esperado (definido por como o laboratório foi montado)
ESPERADO = {9001: "ABERTA", 9002: "ABERTA", 9003: "FECHADA", 9004: "TIMEOUT (sem resposta)"}
EQUIVALENTE_NMAP = {"ABERTA": "open", "FECHADA": "closed", "TIMEOUT": "filtered"}


def rodar_nmap(portas: str) -> tuple[dict[int, str], str]:
    """Roda nmap -sT e devolve ({porta: estado}, versão). Salva a saída bruta como evidência."""
    # cwd=RAIZ + caminho relativo: o cabeçalho gravado pelo Nmap não expõe caminhos da máquina
    p = subprocess.run(["nmap", "-sT", "-Pn", "-p", portas, "-oN", "evidencias/02_nmap_saida_bruta.txt",
                        "-oX", "-", ALVO], capture_output=True, text=True, cwd=RAIZ)
    raiz = ET.fromstring(p.stdout)
    estados = {int(x.get("portid")): x.find("state").get("state") for x in raiz.iter("port")}
    return estados, raiz.get("version", "?")


def main() -> int:
    EVIDENCIAS.mkdir(exist_ok=True)
    portas = ",".join(map(str, ESPERADO))
    servicos = [ServicoTCP(9001).iniciar(), ServicoTCP(9002).iniciar(), PortaSaturada(9004).iniciar()]
    try:
        saida, meu, _ = rodar_scanner(ALVO, "-p", portas, "-t", TIMEOUT)
        if shutil.which("nmap"):
            nmap, versao = rodar_nmap(portas)
        else:
            nmap, versao = {}, None
    finally:
        for s in servicos:
            s.parar()

    linhas = ["| Porta TCP | Estado esperado | Scanner desenvolvido | Nmap (-sT) | Equivalentes? |",
              "|---|---|---|---|---|"]
    for porta, esperado in ESPERADO.items():
        estado = meu[porta]["estado"]
        n = nmap.get(porta, "N/D (nmap não instalado)")
        if porta in nmap:
            ok = "sim" if EQUIVALENTE_NMAP[estado] == n else "NÃO"
        else:
            ok = "-"
        linhas.append(f"| {porta} | {esperado} | {estado} | {n} | {ok} |")

    texto = cabecalho("Comparação: scanner desenvolvido x Nmap -sT")
    texto += f"Comando do scanner: `python portscanner.py {ALVO} -p {portas} -t {TIMEOUT}`\n\n"
    texto += (f"Comando do Nmap: `nmap -sT -Pn -p {portas} {ALVO}` (Nmap {versao})\n\n" if versao else
              "Comando do Nmap: `nmap -sT -Pn -p " + portas + f" {ALVO}` — **NÃO EXECUTADO: nmap não está instalado.**\n\n")
    texto += "\n".join(linhas) + "\n\nEquivalência de estados: ABERTA=open, FECHADA=closed, TIMEOUT=filtered.\n\n"
    texto += "## Saída do scanner desenvolvido\n\n```\n" + saida + "```\n"
    caminho = salvar("02_comparacao_nmap.md", texto)
    print("\n".join(linhas))
    print(f"\nEvidência salva em {caminho}")
    if not versao:
        print("\nATENÇÃO: nmap não encontrado. Instale (sudo apt install nmap) e rode de novo.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
