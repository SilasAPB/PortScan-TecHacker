# Tratamento de erros — as 7 situações do roteiro

Gerado em 2026-11-24 22:26:47 (máquina local, alvo 127.0.0.1)

| Situação | Código de saída (esperado) | Sem Traceback? |
|---|---|---|
| 1. Porta com serviço ativo | 0 (0) | sim |
| 2. Porta sem serviço | 0 (0) | sim |
| 3a. Porta inválida (acima de 65535) | 2 (2) | sim |
| 3b. Porta inválida (texto) | 2 (2) | sim |
| 3c. Porta inválida (zero) | 2 (2) | sim |
| 4a. Intervalo invertido | 2 (2) | sim |
| 4b. Intervalo malformado | 2 (2) | sim |
| 5. Endereço de destino inválido | 2 (2) | sim |
| 5b. Endereço público sem autorização | 2 (2) | sim |
| 6. Timeout de conexão | 0 (0) | sim |
| 6b. Timeout inválido | 2 (2) | sim |
| 7. Interrupção pelo usuário (Ctrl+C / SIGINT) | 130 (130) | sim |

Códigos: 0 = execução normal | 2 = parâmetro inválido | 130 = interrompido (Ctrl+C).

## 1. Porta com serviço ativo

`python portscanner.py 127.0.0.1 -p 9001` → código de saída **0**

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

## 2. Porta sem serviço

`python portscanner.py 127.0.0.1 -p 9003` → código de saída **0**

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 1 | timeout: 1.0s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*  TEMPO   DETALHE
---------  -----  ---------  --------  ------  ---------------------------------------------
127.0.0.1  9003   FECHADA    -         0.1 ms  conexão recusada (RST recebido, ECONNREFUSED)

Resumo: 1/1 portas verificadas em 0.00s — ABERTA=0 FECHADA=1 TIMEOUT=0 ERRO=0
Portas abertas: nenhuma
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
```

## 3a. Porta inválida (acima de 65535)

`python portscanner.py 127.0.0.1 -p 70000` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -p/--portas: porta fora do intervalo permitido: 70000 (válido: 1-65535)
```

## 3b. Porta inválida (texto)

`python portscanner.py 127.0.0.1 -p http` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -p/--portas: porta inválida: 'http' (use números inteiros)
```

## 3c. Porta inválida (zero)

`python portscanner.py 127.0.0.1 -p 0` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -p/--portas: porta fora do intervalo permitido: 0 (válido: 1-65535)
```

## 4a. Intervalo invertido

`python portscanner.py 127.0.0.1 -p 100-50` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -p/--portas: intervalo inválido: '100-50' (o início 100 é maior que o fim 50)
```

## 4b. Intervalo malformado

`python portscanner.py 127.0.0.1 -p 1-2-3` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -p/--portas: intervalo inválido: '1-2-3' (formato: inicio-fim)
```

## 5. Endereço de destino inválido

`python portscanner.py alvo.invalid -p 80` → código de saída **2**

```
Erro: endereço de destino inválido ou não resolvido: 'alvo.invalid' ([Errno -2] Name or service not known)
```

## 5b. Endereço público sem autorização

`python portscanner.py 8.8.8.8 -p 53` → código de saída **2**

```
Erro: 8.8.8.8 é um endereço público. Escaneie apenas sistemas seus ou expressamente autorizados; se for o caso, repita o comando com --autorizado.
```

## 6. Timeout de conexão

`python portscanner.py 127.0.0.1 -p 9004 -t 0.5` → código de saída **0**

```
Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 1 | timeout: 0.5s | simultâneas: 20

ALVO       PORTA  RESULTADO  SERVIÇO*  TEMPO     DETALHE
---------  -----  ---------  --------  --------  ------------------------------------------------------------------------
127.0.0.1  9004   TIMEOUT    -         500.8 ms  sem resposta em 0.5s (causa indeterminada: firewall, perda, lentidão...)

Resumo: 1/1 portas verificadas em 0.50s — ABERTA=0 FECHADA=0 TIMEOUT=1 ERRO=0
Portas abertas: nenhuma
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
! TIMEOUT não significa porta fechada: a causa é indeterminada (filtro de firewall, perda de pacotes, host lento). Tente aumentar -t.
```

## 6b. Timeout inválido

`python portscanner.py 127.0.0.1 -p 80 -t 0` → código de saída **2**

```
usage: portscanner.py [-h] [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO]
                      [--log ARQUIVO] [--ocultar-fechadas] [--autorizado]
                      alvo
portscanner.py: error: argument -t/--timeout: timeout deve ser maior que 0 e no máximo 120 segundos
```

## 7. Interrupção pelo usuário (Ctrl+C / SIGINT)

`python portscanner.py 127.0.0.1 -p 9003,9004,9005-9010 -t 5 -w 1  # + SIGINT após 1 s` → código de saída **130**

```
Interrompido pelo usuário (Ctrl+C). Exibindo resultados parciais (conexões já em andamento terminam em até 5.0s)...

Aviso: use somente em sistemas próprios ou expressamente autorizados.
Alvo: 127.0.0.1 (127.0.0.1) | portas: 8 | timeout: 5.0s | simultâneas: 1

ALVO       PORTA  RESULTADO  SERVIÇO*  TEMPO   DETALHE
---------  -----  ---------  --------  ------  ---------------------------------------------
127.0.0.1  9003   FECHADA    -         0.2 ms  conexão recusada (RST recebido, ECONNREFUSED)

Resumo: 1/8 portas verificadas em 0.97s — ABERTA=0 FECHADA=1 TIMEOUT=0 ERRO=0
Portas abertas: nenhuma
* nome associado à porta pela tabela do sistema; NÃO confirma o serviço real.
```
