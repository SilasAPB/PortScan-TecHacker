# Testes iniciais

Gerado em 2026-11-24 22:26:46 (máquina local, alvo 127.0.0.1)

Montagem: serviços ativos em 9001 e 9002; 9004 saturada (sem resposta); 9003 e 9005 sem nada escutando.

## Verificação pelo sistema operacional — `ss -ltn` (somente linhas relevantes)

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
LISTEN 0      16         127.0.0.1:9001       0.0.0.0:*   
LISTEN 0      16         127.0.0.1:9002       0.0.0.0:*   
LISTEN 1      0          127.0.0.1:9004       0.0.0.0:*   
```

Observação: 9001, 9002 e 9004 aparecem em LISTEN; 9003 e 9005 não aparecem.

## Saída do scanner — `python portscanner.py 127.0.0.1 -p 9001-9005 -t 1`

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 5 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO      DETALHE
---------  -----  ---------  ------------  ---------  ------------------------------------------------------------------------
127.0.0.1  9001   ABERTA     desconhecido  0.4 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9002   ABERTA     desconhecido  0.4 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9003   FECHADA    -             0.3 ms     conexão recusada (RST recebido, ECONNREFUSED)
127.0.0.1  9004   TIMEOUT    -             1001.1 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
127.0.0.1  9005   FECHADA    -             0.1 ms     conexão recusada (RST recebido, ECONNREFUSED)

Resumo: 5/5 portas verificadas em 1.00s — ABERTA=2 FECHADA=2 TIMEOUT=1 ERRO=0
Portas abertas: 9001, 9002
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
! TIMEOUT não significa porta fechada: a causa é indeterminada (filtro de firewall, perda de pacotes, host lento). Tente aumentar -t.
```

Todas as portas conferem com o esperado: **sim**.
