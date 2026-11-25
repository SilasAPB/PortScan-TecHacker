# Comparação: scanner desenvolvido x Nmap -sT

Gerado em 2026-11-24 22:31:50 (máquina local, alvo 127.0.0.1)

Comando do scanner: `python portscanner.py 127.0.0.1 -p 9001,9002,9003,9004 -t 1`

Comando do Nmap: `nmap -sT -Pn -p 9001,9002,9003,9004 127.0.0.1` (Nmap 7.98)

| Porta TCP | Estado esperado | Scanner desenvolvido | Nmap (-sT) | Equivalentes? |
|---|---|---|---|---|
| 9001 | ABERTA | ABERTA | open | sim |
| 9002 | ABERTA | ABERTA | open | sim |
| 9003 | FECHADA | FECHADA | closed | sim |
| 9004 | TIMEOUT (sem resposta) | TIMEOUT | filtered | sim |

Equivalência de estados: ABERTA=open, FECHADA=closed, TIMEOUT=filtered.

## Saída do scanner desenvolvido

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 4 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO      DETALHE
---------  -----  ---------  ------------  ---------  ------------------------------------------------------------------------
127.0.0.1  9001   ABERTA     desconhecido  0.3 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9002   ABERTA     desconhecido  0.1 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9003   FECHADA    -             0.2 ms     conexão recusada (RST recebido, ECONNREFUSED)
127.0.0.1  9004   TIMEOUT    -             1000.8 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)

Resumo: 4/4 portas verificadas em 1.00s — ABERTA=2 FECHADA=1 TIMEOUT=1 ERRO=0
Portas abertas: 9001, 9002
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
! TIMEOUT não significa porta fechada: a causa é indeterminada (filtro de firewall, perda de pacotes, host lento). Tente aumentar -t.
```
