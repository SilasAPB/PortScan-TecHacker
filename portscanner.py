#!/usr/bin/env python3
"""
portscanner.py — Port scanner TCP (TCP Connect) feito apenas com a biblioteca padrão.

Roteiro 4 — Tecnologias Hacker (Insper).

COMO FUNCIONA (resumo)
    Para cada porta, o programa tenta abrir uma conexão TCP com socket.connect().
    O sistema operacional executa o three-way handshake (SYN -> SYN/ACK -> ACK) e o
    resultado da tentativa é interpretado assim:

        connect() retorna normalmente  -> ABERTA   (handshake concluído)
        ConnectionRefusedError (RST)   -> FECHADA  (host respondeu: ninguém escutando)
        socket.timeout                 -> TIMEOUT  (sem resposta no tempo limite; NÃO
                                                    permite concluir que está fechada)
        qualquer outro OSError         -> ERRO     (ex.: rede/host inalcançável)

    Nenhuma biblioteca de scan é usada e o Nmap NÃO é executado por este programa.

ORGANIZAÇÃO DO CÓDIGO (seguindo as etapas sugeridas no roteiro, seção 3.2)
    1. Parâmetros ........ parse_portas(), resolver_alvo(), criar_parser()
    2. Tentativa ......... tentar_conexao()
    3. Interpretação ..... verificar_porta()  (monta o ResultadoPorta)
    4. Execução .......... escanear()         (concorrência limitada)
    5. Apresentação ...... imprimir_tabela(), imprimir_resumo(), salvar_resultados()
    6. Programa .......... main()

Use SOMENTE em sistemas próprios ou expressamente autorizados.
"""

import argparse
import csv
import errno
import ipaddress
import json
import logging
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

# Estados possíveis de uma tentativa de conexão
ABERTA = "ABERTA"
FECHADA = "FECHADA"
TIMEOUT = "TIMEOUT"
ERRO = "ERRO"

PORTA_MIN, PORTA_MAX = 1, 65535
TIMEOUT_PADRAO = 1.0      # segundos
WORKERS_PADRAO = 20       # conexões simultâneas (concorrência limitada)
WORKERS_MAX = 100         # teto para não gerar carga excessiva

log = logging.getLogger("portscanner")


@dataclass
class ResultadoPorta:
    """Resultado da tentativa de conexão em uma porta."""
    alvo: str          # o que o usuário digitou (IP ou hostname)
    ip: str            # IP efetivamente usado
    porta: int
    estado: str        # ABERTA | FECHADA | TIMEOUT | ERRO
    servico: str       # nome associado à porta pelo SO (NÃO confirma o serviço real)
    tempo_ms: float    # duração da tentativa
    detalhe: str       # explicação legível (ex.: errno)


# --------------------------------------------------------------------------- #
# 1. Receber e validar parâmetros
# --------------------------------------------------------------------------- #

def parse_portas(texto: str) -> list[int]:
    """
    Converte '80', '20-25' ou '22,80,8000-8010' em uma lista ordenada e sem
    repetições. Levanta ValueError com mensagem clara se algo for inválido.
    """
    if texto is None or not texto.strip():
        raise ValueError("nenhuma porta informada")

    def como_porta(s: str) -> int:
        s = s.strip()
        if not (s.isascii() and s.isdigit()):
            raise ValueError(f"porta inválida: '{s}' (use números inteiros)")
        n = int(s)
        if not PORTA_MIN <= n <= PORTA_MAX:
            raise ValueError(
                f"porta fora do intervalo permitido: {n} (válido: {PORTA_MIN}-{PORTA_MAX})")
        return n

    portas: set[int] = set()
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            raise ValueError("lista de portas com elemento vazio (vírgula sobrando?)")
        if "-" in parte:
            pedacos = parte.split("-")
            if len(pedacos) != 2:
                raise ValueError(f"intervalo inválido: '{parte}' (formato: inicio-fim)")
            inicio, fim = como_porta(pedacos[0]), como_porta(pedacos[1])
            if inicio > fim:
                raise ValueError(
                    f"intervalo inválido: '{parte}' (o início {inicio} é maior que o fim {fim})")
            portas.update(range(inicio, fim + 1))
        else:
            portas.add(como_porta(parte))
    return sorted(portas)


def resolver_alvo(alvo: str) -> tuple[int, str]:
    """
    Resolve IP/hostname UMA vez (evita uma consulta DNS por porta).
    Retorna (família, ip). Prefere IPv4 quando o nome tem os dois.
    Levanta ValueError se o endereço for inválido/irresolvível.
    """
    if not alvo or not alvo.strip():
        raise ValueError("endereço de destino vazio")
    try:
        infos = socket.getaddrinfo(alvo.strip(), None, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as e:
        raise ValueError(f"endereço de destino inválido ou não resolvido: '{alvo}' ({e})")
    infos.sort(key=lambda i: 0 if i[0] == socket.AF_INET else 1)
    familia, _, _, _, sockaddr = infos[0]
    return familia, sockaddr[0]


def alvo_nao_publico(ip: str) -> bool:
    """True para loopback, rede privada, link-local etc. (alvos 'de laboratório')."""
    try:
        return not ipaddress.ip_address(ip.split("%")[0]).is_global
    except ValueError:
        return False


def _tipo_portas(texto: str) -> list[int]:
    try:
        return parse_portas(texto)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def _tipo_timeout(texto: str) -> float:
    try:
        v = float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"timeout inválido: '{texto}' (use um número, ex.: 0.5)")
    if not 0 < v <= 120:
        raise argparse.ArgumentTypeError("timeout deve ser maior que 0 e no máximo 120 segundos")
    return v


def _tipo_workers(texto: str) -> int:
    try:
        v = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"valor inválido: '{texto}' (use um inteiro)")
    if not 1 <= v <= WORKERS_MAX:
        raise argparse.ArgumentTypeError(f"deve estar entre 1 e {WORKERS_MAX}")
    return v


def _tipo_saida(texto: str) -> str:
    if not texto.lower().endswith((".json", ".csv")):
        raise argparse.ArgumentTypeError("a extensão do arquivo deve ser .json ou .csv")
    return texto


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="portscanner.py",
        description="Port scanner TCP Connect (Roteiro 4 — Tecnologias Hacker). "
                    "Use somente em sistemas próprios ou expressamente autorizados.",
        epilog="exemplos:\n"
               "  python portscanner.py 127.0.0.1 -p 80\n"
               "  python portscanner.py localhost -p 20-25,80,443 -t 0.5\n"
               "  python portscanner.py 192.168.0.10 -p 1-1024 -w 50 -o resultado.json --log scan.log\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("alvo", help="endereço IP ou hostname de destino")
    p.add_argument("-p", "--portas", type=_tipo_portas, default=parse_portas("1-1024"),
                   metavar="PORTAS",
                   help="porta, intervalo e/ou lista: 80 | 20-25 | 22,80,8000-8010 (padrão: 1-1024)")
    p.add_argument("-t", "--timeout", type=_tipo_timeout, default=TIMEOUT_PADRAO, metavar="SEG",
                   help=f"tempo limite por tentativa em segundos (padrão: {TIMEOUT_PADRAO})")
    p.add_argument("-w", "--workers", type=_tipo_workers, default=WORKERS_PADRAO, metavar="N",
                   help=f"tentativas simultâneas, 1-{WORKERS_MAX} (padrão: {WORKERS_PADRAO}; "
                        "use 1 para execução sequencial)")
    p.add_argument("-o", "--saida", type=_tipo_saida, metavar="ARQUIVO",
                   help="salva os resultados em ARQUIVO.json ou ARQUIVO.csv")
    p.add_argument("--log", metavar="ARQUIVO",
                   help="grava um log com cada tentativa realizada e os erros")
    p.add_argument("--ocultar-fechadas", action="store_true",
                   help="não lista portas FECHADAS (elas continuam contadas no resumo)")
    p.add_argument("--autorizado", action="store_true",
                   help="confirma que você tem autorização para escanear um alvo de IP público")
    return p


# --------------------------------------------------------------------------- #
# 2. Tentativa de conexão
# --------------------------------------------------------------------------- #

def tentar_conexao(familia: int, ip: str, porta: int, timeout: float) -> tuple[str, str]:
    """
    Faz UMA tentativa de conexão TCP e devolve (estado, detalhe).
    O 'with' garante que o socket é sempre fechado (libera o recurso), mesmo em erro.
    A ORDEM dos except importa: ConnectionRefusedError e TimeoutError são subclasses de
    OSError, então precisam vir antes do except OSError genérico.
    """
    try:
        with socket.socket(familia, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)          # controla o tempo de espera do connect()
            s.connect((ip, porta))         # dispara o handshake TCP
        return ABERTA, "conexão TCP estabelecida (handshake concluído)"
    except ConnectionRefusedError:
        return FECHADA, "conexão recusada (RST recebido, ECONNREFUSED)"
    except TimeoutError:                   # socket.timeout é alias de TimeoutError
        return TIMEOUT, f"sem resposta em {timeout}s (causa indeterminada: firewall, perda, lentidão...)"
    except OSError as e:
        nome = errno.errorcode.get(e.errno, "?")
        return ERRO, f"{nome}: {e.strerror or e}"


# --------------------------------------------------------------------------- #
# 3. Interpretar o resultado
# --------------------------------------------------------------------------- #

def nome_servico(porta: int) -> str:
    """Nome 'normalmente associado' à porta (tabela do SO). NÃO confirma o serviço real."""
    try:
        return socket.getservbyport(porta, "tcp")
    except OSError:
        return "desconhecido"


def verificar_porta(alvo: str, familia: int, ip: str, porta: int, timeout: float) -> ResultadoPorta:
    """Tenta a conexão, mede o tempo e monta o resultado. Nunca levanta exceção."""
    inicio = time.perf_counter()
    try:
        estado, detalhe = tentar_conexao(familia, ip, porta, timeout)
    except Exception as e:  # rede de segurança: uma porta com problema não derruba as demais
        estado, detalhe = ERRO, f"falha inesperada: {type(e).__name__}: {e}"
    tempo_ms = (time.perf_counter() - inicio) * 1000
    servico = nome_servico(porta) if estado == ABERTA else "-"
    resultado = ResultadoPorta(alvo, ip, porta, estado, servico, round(tempo_ms, 1), detalhe)

    nivel = {ABERTA: logging.INFO, FECHADA: logging.INFO,
             TIMEOUT: logging.WARNING, ERRO: logging.ERROR}[estado]
    log.log(nivel, "alvo=%s ip=%s porta=%d resultado=%s tempo_ms=%.1f detalhe=%s",
            alvo, ip, porta, estado, tempo_ms, detalhe)
    return resultado


# --------------------------------------------------------------------------- #
# 4. Execução (concorrência com limite)
# --------------------------------------------------------------------------- #

def escanear(alvo: str, familia: int, ip: str, portas: list[int], timeout: float,
             workers: int, resultados: list[ResultadoPorta]) -> None:
    """
    Verifica as portas usando no máximo `workers` threads simultâneas.
    Os resultados são acrescentados em `resultados` à medida que ficam prontos; assim,
    se o usuário interromper (Ctrl+C), o que já foi coletado não se perde.
    """
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        futuros = [pool.submit(verificar_porta, alvo, familia, ip, p, timeout) for p in portas]
        for f in as_completed(futuros):
            resultados.append(f.result())
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)   # descarta o que ainda não começou
        raise
    pool.shutdown()


# --------------------------------------------------------------------------- #
# 5. Registrar e apresentar
# --------------------------------------------------------------------------- #

def imprimir_tabela(resultados: list[ResultadoPorta], ocultar_fechadas: bool) -> None:
    linhas = [r for r in sorted(resultados, key=lambda r: r.porta)
              if not (ocultar_fechadas and r.estado == FECHADA)]
    if not linhas:
        print("(nenhuma porta para listar)")
        return
    cab = ("ALVO", "PORTA", "RESULTADO", "SERVIÇO*", "TEMPO", "DETALHE")
    dados = [(r.ip if r.ip == r.alvo else f"{r.alvo} ({r.ip})", str(r.porta), r.estado,
              r.servico, f"{r.tempo_ms:.1f} ms", r.detalhe) for r in linhas]
    larg = [max(len(cab[i]), *(len(d[i]) for d in dados)) for i in range(len(cab))]
    fmt = lambda t: "  ".join(c.ljust(larg[i]) for i, c in enumerate(t)).rstrip()
    print(fmt(cab))
    print("  ".join("-" * w for w in larg))
    for d in dados:
        print(fmt(d))


def contar(resultados: list[ResultadoPorta]) -> dict[str, int]:
    c = {ABERTA: 0, FECHADA: 0, TIMEOUT: 0, ERRO: 0}
    for r in resultados:
        c[r.estado] += 1
    return c


def imprimir_resumo(resultados: list[ResultadoPorta], total: int, duracao: float) -> None:
    c = contar(resultados)
    print()
    print(f"Resumo: {len(resultados)}/{total} portas verificadas em {duracao:.2f}s — "
          f"ABERTA={c[ABERTA]} FECHADA={c[FECHADA]} TIMEOUT={c[TIMEOUT]} ERRO={c[ERRO]}")
    abertas = sorted(r.porta for r in resultados if r.estado == ABERTA)
    print(f"Portas abertas: {', '.join(map(str, abertas)) if abertas else 'nenhuma'}")
    print("* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.")
    if c[TIMEOUT]:
        print("! TIMEOUT não significa porta fechada: a causa é indeterminada "
              "(filtro de firewall, perda de pacotes, host lento). Tente aumentar -t.")


def salvar_resultados(caminho: str, meta: dict, resultados: list[ResultadoPorta]) -> None:
    linhas = [asdict(r) for r in sorted(resultados, key=lambda r: r.porta)]
    if caminho.lower().endswith(".json"):
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "resultados": linhas}, f, ensure_ascii=False, indent=2)
    else:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ResultadoPorta.__dataclass_fields__))
            w.writeheader()
            w.writerows(linhas)


def configurar_log(caminho: str | None) -> None:
    if not caminho:
        log.addHandler(logging.NullHandler())
        return
    h = logging.FileHandler(caminho, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    log.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# 6. Programa principal
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    """Códigos de saída: 0 ok | 1 falha ao salvar arquivo | 2 parâmetro inválido | 130 Ctrl+C"""
    args = criar_parser().parse_args(argv)     # argparse já trata portas/timeout/workers inválidos

    try:
        configurar_log(args.log)
    except OSError as e:
        print(f"Erro: não foi possível abrir o arquivo de log: {e}", file=sys.stderr)
        return 2

    try:
        familia, ip = resolver_alvo(args.alvo)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2

    if not alvo_nao_publico(ip) and not args.autorizado:
        print(f"Erro: {ip} é um endereço público. Escaneie apenas sistemas seus ou "
              "expressamente autorizados; se for o caso, repita o comando com --autorizado.",
              file=sys.stderr)
        return 2

    print("Aviso: use somente em sistemas próprios ou expressamente autorizados.")
    print(f"Alvo: {args.alvo} ({ip}) | portas: {len(args.portas)} | timeout: {args.timeout}s | "
          f"simultâneas: {args.workers}\n")
    log.info("inicio alvo=%s ip=%s portas=%d timeout=%s workers=%d",
             args.alvo, ip, len(args.portas), args.timeout, args.workers)

    resultados: list[ResultadoPorta] = []
    inicio_iso = datetime.now().isoformat(timespec="seconds")
    inicio = time.perf_counter()
    interrompido = False
    try:
        escanear(args.alvo, familia, ip, args.portas, args.timeout, args.workers, resultados)
    except KeyboardInterrupt:
        interrompido = True
        print("\nInterrompido pelo usuário (Ctrl+C). Exibindo resultados parciais "
              f"(conexões já em andamento terminam em até {args.timeout}s)...\n", file=sys.stderr)
        log.warning("interrompido pelo usuario")
    duracao = time.perf_counter() - inicio

    imprimir_tabela(resultados, args.ocultar_fechadas)
    imprimir_resumo(resultados, len(args.portas), duracao)
    log.info("fim duracao=%.2fs verificadas=%d/%d", duracao, len(resultados), len(args.portas))

    codigo = 130 if interrompido else 0
    if args.saida:
        meta = {"alvo": args.alvo, "ip": ip, "inicio": inicio_iso, "duracao_s": round(duracao, 3),
                "timeout_s": args.timeout, "workers": args.workers,
                "portas_solicitadas": len(args.portas), "portas_verificadas": len(resultados),
                "interrompido": interrompido}
        try:
            salvar_resultados(args.saida, meta, resultados)
            print(f"Resultados salvos em: {args.saida}")
        except OSError as e:
            print(f"Erro: não foi possível salvar '{args.saida}': {e}", file=sys.stderr)
            codigo = codigo or 1
    return codigo


if __name__ == "__main__":
    sys.exit(main())
