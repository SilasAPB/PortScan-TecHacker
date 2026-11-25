"""Utilidades compartilhadas pelos scripts de experimento (não é um experimento)."""

import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIAS = RAIZ / "evidencias"
SCANNER = RAIZ / "portscanner.py"

# permite `from lab.servidor_teste import ...` a partir de qualquer pasta
sys.path.insert(0, str(RAIZ))


def rodar_scanner(*args: str) -> tuple[str, dict[int, dict], int]:
    """
    Executa o scanner como o usuário executaria (linha de comando).
    Retorna (stdout, {porta: resultado}, código_de_saída). Usa --saida JSON só para
    ler os resultados estruturados de volta.
    """
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "r.json"
        p = subprocess.run([sys.executable, str(SCANNER), *args, "-o", str(saida)],
                           capture_output=True, text=True)
        por_porta = {}
        if saida.exists():
            dados = json.loads(saida.read_text(encoding="utf-8"))
            por_porta = {r["porta"]: r for r in dados["resultados"]}
    # remove a linha do arquivo temporário (detalhe interno deste helper, não do scanner)
    texto = "".join(l for l in (p.stdout + p.stderr).splitlines(keepends=True)
                    if not l.startswith("Resultados salvos em:"))
    return texto, por_porta, p.returncode


def comando(*args: str) -> str:
    """Executa um comando do SO e devolve a saída (ou o motivo de não ter rodado)."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return f"(comando '{args[0]}' não encontrado)"


def salvar(nome: str, texto: str) -> Path:
    EVIDENCIAS.mkdir(exist_ok=True)
    caminho = EVIDENCIAS / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def cabecalho(titulo: str) -> str:
    return f"# {titulo}\n\nGerado em {datetime.now():%Y-%m-%d %H:%M:%S} (máquina local, alvo 127.0.0.1)\n\n"
