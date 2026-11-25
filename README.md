# Port Scanner TCP — Roteiro 4 (Tecnologias Hacker · Insper)

Scanner de portas **TCP Connect** escrito em Python 3 usando apenas a biblioteca padrão (`socket`, `argparse`,
`concurrent.futures`...). Nenhuma biblioteca de scan é usada e o Nmap **não** é executado pelo programa — ele só
aparece como ferramenta de validação nos experimentos.

> ⚠️ **Uso ético:** escaneie somente sistemas **próprios ou expressamente autorizados**. Por segurança, o programa
> recusa alvos de IP público a menos que você passe `--autorizado`.

## Requisitos

- Python **3.10+** (testado em 3.14) — sem dependências externas (`pip install` não é necessário)
- Linux/macOS/Windows. Os experimentos usam `ss` (Linux) para checar portas em escuta
- Para a comparação da seção 5: `nmap` (`sudo apt install nmap`)

## Início rápido

```bash
# 1) terminal A: sobe o laboratório local (portas 9001 e 9002 abertas; 9004 gera timeout)
python lab/servidor_teste.py

# 2) terminal B: escaneia
python portscanner.py 127.0.0.1 -p 9001-9004 -t 1
```

Saída esperada (resumida):

```
ALVO       PORTA  RESULTADO  SERVIÇO*      TEMPO      DETALHE
127.0.0.1  9001   ABERTA     desconhecido  0.6 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9002   ABERTA     desconhecido  0.6 ms     conexão TCP estabelecida (handshake concluído)
127.0.0.1  9003   FECHADA    -             0.3 ms     conexão recusada (RST recebido, ECONNREFUSED)
127.0.0.1  9004   TIMEOUT    -             1000.9 ms  sem resposta em 1.0s (causa indeterminada: ...)
```

## Parâmetros

```
python portscanner.py ALVO [-p PORTAS] [-t SEG] [-w N] [-o ARQUIVO] [--log ARQUIVO]
                           [--ocultar-fechadas] [--autorizado] [-h]
```

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `ALVO` | endereço IP ou hostname (resolvido uma vez; IPv4 preferido) | — (obrigatório) |
| `-p`, `--portas` | porta, intervalo e/ou lista: `80`, `20-25`, `22,80,8000-8010` (válido: 1–65535) | `1-1024` |
| `-t`, `--timeout` | tempo limite por tentativa, em segundos (0 < t ≤ 120) | `1.0` |
| `-w`, `--workers` | tentativas simultâneas (1–100). `1` = sequencial | `20` |
| `-o`, `--saida` | grava resultados em `.json` ou `.csv` (pela extensão) | — |
| `--log` | grava log de cada tentativa e dos erros | — |
| `--ocultar-fechadas` | não lista portas FECHADAS (continuam no resumo) | — |
| `--autorizado` | confirma autorização para alvo de IP público | — |

**Resultados possíveis por porta**

| Estado | Significa | Observação |
|---|---|---|
| `ABERTA` | handshake TCP concluído | não diz qual serviço é, nem se é vulnerável |
| `FECHADA` | recebeu RST (`ConnectionRefused`) | o host respondeu: nada escutando |
| `TIMEOUT` | sem resposta dentro de `-t` | **não** equivale a fechada (firewall, perda, lentidão) |
| `ERRO` | outro erro de rede (ex.: `ENETUNREACH`) | o `errno` aparece em DETALHE |

**Códigos de saída:** `0` ok · `1` falha ao salvar arquivo · `2` parâmetro/alvo inválido · `130` interrompido (Ctrl+C)

## Exemplos

```bash
python portscanner.py 127.0.0.1 -p 80                          # uma porta
python portscanner.py localhost -p 20-25,80,443 -t 0.5         # intervalo + lista, timeout menor
python portscanner.py 127.0.0.1 -p 1-1024 -w 50 --ocultar-fechadas
python portscanner.py 127.0.0.1 -p 9001-9004 -o resultado.json --log scan.log
python portscanner.py 127.0.0.1 -p 9001-9004 -o resultado.csv
python portscanner.py --help
```

## Melhorias implementadas (seção 7)

O roteiro pede ao menos uma; foram implementadas seis, todas demonstradas em `evidencias/06_melhorias.md`:

| # | Melhoria | Como usar | Evidência |
|---|---|---|---|
| M1 | **Execução concorrente com limite** (pool de threads, teto 100) | `-w N` | 4 portas com timeout de 1 s: 4,01 s sequencial → 1,00 s com `-w 6` |
| M2 | **Exportação** JSON/CSV (com metadados da execução) | `-o arq.json` / `-o arq.csv` | `06_exemplo.json`, `06_exemplo.csv` |
| M3 | **Medição de desempenho** (duração total e tempo por porta) | automático | resumo + `meta.duracao_s` |
| M4 | **Identificação de serviços** pelo nome associado à porta, com aviso de que não confirma o serviço real | automático (portas abertas) | coluna `SERVIÇO*` |
| M5 | **CLI com `argparse`** e mensagens de ajuda/validação | `--help` | `06_melhorias.md` |
| M6 | **Registro de execução** em arquivo de log | `--log arq.log` | `06_exemplo.log` |

Além disso: trava de segurança para IP público (`--autorizado`) e tratamento de Ctrl+C com resultados parciais.

## Estrutura do repositório

```
.
├── README.md                  ← você está aqui (instruções de execução)
├── ENTREGA.md                 ← mapa: item do roteiro → o que foi feito → onde está
├── portscanner.py             ← o scanner (código-fonte entregável)
├── lab/servidor_teste.py      ← ambiente de teste local (portas abertas / fechada / timeout)
├── experimentos/              ← scripts que geram as evidências (um por seção do roteiro)
├── tests/test_portscanner.py  ← 15 testes automatizados
├── evidencias/                ← saídas reais dos experimentos (geradas pelos scripts)
├── relatorio/relatorio.md     ← relatório técnico (2–3 páginas)
├── docs/planejamento.md       ← estratégia, pseudocódigo e fluxograma (seção 2)
├── docs/guia_demonstracao.md  ← roteiro da demonstração + explicação do código
└── rodar_tudo.sh              ← roda testes + experimentos e regenera evidencias/
```

## Reproduzindo tudo

```bash
python -m unittest discover -s tests -v   # testes automatizados
./rodar_tudo.sh                           # todos os experimentos -> evidencias/
python experimentos/comparar_nmap.py      # seção 5 (precisa do nmap instalado)
```

## Como o laboratório gera cada estado (sem root)

- **ABERTA** — `ServicoTCP` escuta e aceita conexões.
- **FECHADA** — basta não haver nada escutando: o SO responde RST.
- **TIMEOUT** — `PortaSaturada` escuta com `listen(0)` e **nunca chama `accept()`**: com a fila de conexões cheia, o
  kernel Linux descarta os SYNs seguintes em silêncio, exatamente como um firewall com `DROP`. (Comportamento
  específico do Linux; em outros SOs o experimento de timeout pode se comportar diferente.)
