# Melhorias implementadas

Gerado em 2026-11-24 22:27:11 (máquina local, alvo 127.0.0.1)

## M1 + M3 — Concorrência com limite e medição de desempenho

Alvo: 4 portas que não respondem (cada uma custa `-t 1` = 1 s) + 2 abertas.

| Execução | Parâmetro | Duração total |
|---|---|---|
| Sequencial | `-w 1` | 4.00 s |
| Concorrente | `-w 6` | 1.00 s |

Ganho observado: ~4.0x. O teto de `-w` é 100 para não gerar carga excessiva.

Saída da execução concorrente:

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 6 | timeout: 1.0s | simultâneas: 6

ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO      DETALHE
---------  -----  ---------  ------------  ---------  ------------------------------------------------------------------------
127.0.0.1  6379   ABERTA     redis         0.3 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9001   ABERTA     desconhecido  0.3 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9004   TIMEOUT    -             1000.7 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
127.0.0.1  9005   TIMEOUT    -             1001.2 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
127.0.0.1  9006   TIMEOUT    -             1000.9 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
127.0.0.1  9007   TIMEOUT    -             1001.3 ms  sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)

Resumo: 6/6 portas verificadas em 1.00s — ABERTA=2 FECHADA=0 TIMEOUT=4 ERRO=0
Portas abertas: 6379, 9001
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
! TIMEOUT não significa porta fechada: a causa é indeterminada (filtro de firewall, perda de pacotes, host lento). Tente aumentar -t.
Resultados salvos em: evidencias/06_exemplo.json
```

## M4 — Identificação de serviços (e por que ela não prova nada)

A porta 6379 recebeu um serviço de teste que **não é Redis** (só envia um banner de texto); mesmo assim o scanner exibe o nome `redis`, pois o nome vem da tabela de portas do SO. Por isso a coluna é marcada com `*` e o rodapé avisa que o nome não confirma o serviço real.

## M2 — Exportação

`06_exemplo.json` e `06_exemplo.csv` (mesma execução, formatos diferentes).

```
alvo,ip,porta,estado,servico,tempo_ms,detalhe
127.0.0.1,127.0.0.1,6379,ABERTA,"# Local services
",0.4,conexão TCP estabelecida (handshake concluído)
127.0.0.1,127.0.0.1,9001,ABERTA,desconhecido,0.2,conexão TCP estabelecida (handshake concluído)
127.0.0.1,127.0.0.1,9004,TIMEOUT,-,1000.3,"sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)"
127.0.0.1,127.0.0.1,9005,TIMEOUT,-,1001.1,"sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)"
127.0.0.1,127.0.0.1,9006,TIMEOUT,-,1001.3,"sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)"
127.0.0.1,127.0.0.1,9007,TIMEOUT,-,1001.0,"sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)"
```

## M6 — Log de execução

`06_exemplo.log` (cada tentativa e eventuais erros):

```
2026-11-24 22:24:16,086 INFO inicio alvo=127.0.0.1 ip=127.0.0.1 portas=6 timeout=1.0 workers=6
2026-11-24 22:24:16,087 INFO alvo=127.0.0.1 ip=127.0.0.1 porta=9001 resultado=ABERTA tempo_ms=0.3 detalhe=conexão TCP estabelecida (handshake concluído)
2026-11-24 22:24:16,087 INFO alvo=127.0.0.1 ip=127.0.0.1 porta=6379 resultado=ABERTA tempo_ms=0.5 detalhe=conexão TCP estabelecida (handshake concluído)
2026-11-24 22:24:17,088 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9007 resultado=TIMEOUT tempo_ms=1000.8 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:24:17,088 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9006 resultado=TIMEOUT tempo_ms=1001.2 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:24:17,088 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9004 resultado=TIMEOUT tempo_ms=1001.3 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:24:17,088 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9005 resultado=TIMEOUT tempo_ms=1001.4 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:24:17,088 INFO fim duracao=1.00s verificadas=6/6
2026-11-24 22:27:08,735 INFO inicio alvo=127.0.0.1 ip=127.0.0.1 portas=6 timeout=1.0 workers=6
2026-11-24 22:27:08,736 INFO alvo=127.0.0.1 ip=127.0.0.1 porta=6379 resultado=ABERTA tempo_ms=0.3 detalhe=conexão TCP estabelecida (handshake concluído)
2026-11-24 22:27:08,736 INFO alvo=127.0.0.1 ip=127.0.0.1 porta=9001 resultado=ABERTA tempo_ms=0.3 detalhe=conexão TCP estabelecida (handshake concluído)
2026-11-24 22:27:09,737 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9004 resultado=TIMEOUT tempo_ms=1000.7 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:27:09,737 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9006 resultado=TIMEOUT tempo_ms=1000.9 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:27:09,737 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9005 resultado=TIMEOUT tempo_ms=1001.2 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:27:09,738 WARNING alvo=127.0.0.1 ip=127.0.0.1 porta=9007 resultado=TIMEOUT tempo_ms=1001.3 detalhe=sem resposta em 1.0s (causa indeterminada: firewall, perda, lentidão...)
2026-11-24 22:27:09,739 INFO fim duracao=1.00s verificadas=6/6
```

## M5 — Interface de linha de comando

`python portscanner.py --help`:

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo

Port scanner TCP Connect (Roteiro 4 — Tecnologias Hacker). Use somente em sistemas próprios ou expressamente autorizados.

positional arguments:
  alvo                 endereço IP ou hostname de destino

options:
  -h, --help           show this help message and exit
  -p, --portas PORTAS  porta, intervalo e/ou lista: 80 | 20-25 |
                       22,80,8000-8010 (padrão: 1-1024)
  -t, --timeout SEG    tempo limite por tentativa em segundos (padrão: 1.0)
  -w, --workers N      tentativas simultâneas, 1-100 (padrão: 20; use 1 para
                       execução sequencial)
  -o, --saida ARQUIVO  salva os resultados em ARQUIVO.json ou ARQUIVO.csv
  --log ARQUIVO        grava um log com cada tentativa realizada e os erros
  --ocultar-fechadas   não lista portas FECHADAS (elas continuam contadas no
                       resumo)
  --autorizado         confirma que você tem autorização para escanear um alvo
                       de IP público

exemplos:
  python portscanner.py 127.0.0.1 -p 80
  python portscanner.py localhost -p 20-25,80,443 -t 0.5
  python portscanner.py 192.168.0.10 -p 1-1024 -w 50 -o resultado.json --log scan.log
```
