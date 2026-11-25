# Experimento de mudança de estado do serviço

Gerado em 2026-11-24 22:26:55 (máquina local, alvo 127.0.0.1)

Porta testada: 127.0.0.1:9001

| Rodada | Esperado | Scanner | Tempo (ms) | Confere? |
|---|---|---|---|---|
| A — serviço ativo | ABERTA | ABERTA | 0.2 | sim |
| B — serviço interrompido | FECHADA | FECHADA | 0.2 | sim |
| C — serviço reiniciado | ABERTA | ABERTA | 0.1 | sim |

## Rodada A — serviço ativo

Verificação independente do SO — `ss -ltn "sport = :9001"`:

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      16         127.0.0.1:9001      0.0.0.0:*
```

Saída do scanner:

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 1 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO   DETALHE
---------  -----  ---------  ------------  ------  ----------------------------------------------
127.0.0.1  9001   ABERTA     desconhecido  0.2 ms  conexão TCP estabelecida (handshake concluído)

Resumo: 1/1 portas verificadas em 0.00s — ABERTA=1 FECHADA=0 TIMEOUT=0 ERRO=0
Portas abertas: 9001
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
```

## Rodada B — serviço interrompido

Verificação independente do SO — `ss -ltn "sport = :9001"`:

```
State Recv-Q Send-Q Local Address:Port Peer Address:Port
```

Saída do scanner:

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 1 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*  TEMPO   DETALHE
---------  -----  ---------  --------  ------  ---------------------------------------------
127.0.0.1  9001   FECHADA    -         0.2 ms  conexão recusada (RST recebido, ECONNREFUSED)

Resumo: 1/1 portas verificadas em 0.00s — ABERTA=0 FECHADA=1 TIMEOUT=0 ERRO=0
Portas abertas: nenhuma
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
```

## Rodada C — serviço reiniciado

Verificação independente do SO — `ss -ltn "sport = :9001"`:

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      16         127.0.0.1:9001      0.0.0.0:*
```

Saída do scanner:

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 1 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO   DETALHE
---------  -----  ---------  ------------  ------  ----------------------------------------------
127.0.0.1  9001   ABERTA     desconhecido  0.1 ms  conexão TCP estabelecida (handshake concluído)

Resumo: 1/1 portas verificadas em 0.00s — ABERTA=1 FECHADA=0 TIMEOUT=0 ERRO=0
Portas abertas: 9001
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
```
