#!/usr/bin/env python3
"""
lab/servidor_teste.py — Ambiente de teste local (127.0.0.1) para o port scanner.

Cria, na SUA máquina, os três comportamentos que o scanner precisa distinguir:

    ServicoTCP       -> porta ABERTA   (alguém escuta e aceita conexões)
    (nada escutando) -> porta FECHADA  (o SO responde RST -> "connection refused")
    PortaSaturada    -> TIMEOUT        (fila de conexões cheia: o kernel descarta os SYNs
                                        e o cliente nunca recebe resposta, igual a um
                                        firewall com DROP — sem precisar de root/iptables)

Uso manual (deixe rodando em um terminal e escaneie em outro):
    python lab/servidor_teste.py --abertas 9001 9002 --saturada 9004
    python portscanner.py 127.0.0.1 -p 9001-9004 -t 1

Para o experimento de "mudança de estado" basta dar Ctrl+C neste programa (serviço
interrompido) e subir de novo (serviço reiniciado).

Também é importado pelos scripts da pasta experimentos/.
"""

import argparse
import socket
import sys
import threading
import time

HOST_PADRAO = "127.0.0.1"


class ServicoTCP:
    """Serviço TCP mínimo: aceita conexões, envia um banner curto e fecha."""

    def __init__(self, porta: int, host: str = HOST_PADRAO):
        self.porta, self.host = porta, host
        self._sock: socket.socket | None = None
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None

    def iniciar(self) -> "ServicoTCP":
        self._parar.clear()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # permite reiniciar rápido
        s.bind((self.host, self.porta))
        s.listen(16)
        s.settimeout(0.2)                                          # para checar o evento de parada
        self._sock = s
        self._thread = threading.Thread(target=self._aceitar, daemon=True)
        self._thread.start()
        return self

    def _aceitar(self) -> None:
        while not self._parar.is_set():
            try:
                cliente, _ = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with cliente:
                try:
                    cliente.sendall(f"SERVIDOR-DE-TESTE porta={self.porta}\r\n".encode())
                except OSError:
                    pass

    def parar(self) -> None:
        """Fecha o socket de escuta: a porta passa a responder 'connection refused'."""
        self._parar.set()
        if self._thread:
            self._thread.join()
        if self._sock:
            self._sock.close()
            self._sock = None


class PortaSaturada:
    """
    Porta que LISTA mas cujo accept-queue está cheio.
    Em Linux, com listen(0) cabe 1 conexão pendente; enquanto ninguém chamar accept(),
    novos SYNs são descartados em silêncio -> o cliente só vê TIMEOUT.
    liberar() passa a aceitar tudo (simula um serviço que 'acordou'): o SYN retransmitido
    pelo cliente (~1 s depois) já passa a ser aceito.
    """

    def __init__(self, porta: int, host: str = HOST_PADRAO):
        self.porta, self.host = porta, host
        self._sock: socket.socket | None = None
        self._clientes: list[socket.socket] = []
        self._servico: ServicoTCP | None = None

    def iniciar(self) -> "PortaSaturada":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.porta))
        s.listen(0)
        self._sock = s
        # Enche a fila: conecta até uma tentativa estourar o tempo (= fila cheia).
        for _ in range(5):
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.settimeout(0.3)
            try:
                c.connect((self.host, self.porta))
                self._clientes.append(c)          # ocupa a vaga na fila
            except TimeoutError:
                c.close()
                break
        return self

    def liberar(self) -> None:
        """Esvazia a fila e passa a atender normalmente na mesma porta."""
        if self._sock is None:
            return
        self._sock.close()                         # entrega a porta ao ServicoTCP
        self._sock = None
        for c in self._clientes:
            c.close()
        self._clientes.clear()
        self._servico = ServicoTCP(self.porta, self.host).iniciar()

    def parar(self) -> None:
        if self._servico:
            self._servico.parar()
            self._servico = None
        for c in self._clientes:
            c.close()
        self._clientes.clear()
        if self._sock:
            self._sock.close()
            self._sock = None


def main() -> int:
    ap = argparse.ArgumentParser(description="Ambiente de teste local para o port scanner.")
    ap.add_argument("--host", default=HOST_PADRAO, help=f"interface local (padrão {HOST_PADRAO})")
    ap.add_argument("--abertas", type=int, nargs="*", default=[9001, 9002],
                    help="portas com serviço ativo (padrão: 9001 9002)")
    ap.add_argument("--saturada", type=int, nargs="*", default=[9004],
                    help="portas que geram TIMEOUT (padrão: 9004)")
    args = ap.parse_args()

    ativos = []
    try:
        for p in args.abertas:
            ativos.append(ServicoTCP(p, args.host).iniciar())
            print(f"[ABERTA ] {args.host}:{p}  serviço de teste ativo")
        for p in args.saturada:
            ativos.append(PortaSaturada(p, args.host).iniciar())
            print(f"[TIMEOUT] {args.host}:{p}  fila de conexões saturada (SYNs descartados)")
        print("\nQualquer outra porta responde FECHADA. Ctrl+C para encerrar.\n")
        while True:
            time.sleep(1)
    except OSError as e:
        print(f"Erro ao iniciar o laboratório: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nEncerrando serviços de teste...")
    finally:
        for a in ativos:
            a.parar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
