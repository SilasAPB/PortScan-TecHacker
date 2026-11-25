# Efeito do tempo limite (timeout) no resultado

Gerado em 2026-11-24 22:26:55 (máquina local, alvo 127.0.0.1)

| Cenário | Timeout (-t) | Resultado | Tempo (ms) | A porta estava realmente... |
|---|---|---|---|---|
| 1. Nunca responde (DROP) | 0.5 s | TIMEOUT | 500.4 | inacessível |
| 1. Nunca responde (DROP) | 3 s | TIMEOUT | 3003.0 | inacessível |
| 2. Serviço volta após 0,4 s | 0.5 s | TIMEOUT | 500.8 | ABERTA (serviço voltou) |
| 2. Serviço volta após 0,4 s | 3 s | ABERTA | 1010.3 | ABERTA (serviço voltou) |

Leitura: no cenário 2 a mesma porta aparece como TIMEOUT com `-t 0.5` e como ABERTA com `-t 3`. Logo, TIMEOUT só informa que não houve resposta *dentro do tempo escolhido*.
