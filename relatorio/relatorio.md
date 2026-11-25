# Relatório Técnico — Port Scanner TCP

**Disciplina:** Tecnologias Hacker · Roteiro 4  **Aluno:** _________________________  **Data:** ___/___/______
**Ambiente:** Linux, Python 3.14, alvo `127.0.0.1` (laboratório próprio). Todos os testes foram feitos apenas em
sistemas sob meu controle. Código, evidências brutas e instruções: ver `README.md` e `evidencias/`.

## 1. Estratégia de implementação

O scanner é do tipo **TCP Connect**: para cada porta, `socket.connect()` pede ao SO que complete um
*three-way handshake* e o programa interpreta o desfecho. Foram usados `socket.socket` (cria o socket TCP),
`settimeout` (limita a espera), `getaddrinfo` (resolve o alvo uma vez), `with` (fecha o socket mesmo em erro) e
`errno` (detalha falhas). Nenhuma biblioteca de scan é usada e o Nmap não é chamado pelo programa.

| Desfecho | Na rede | Exceção Python | Estado |
|---|---|---|---|
| Conexão aceita | SYN → SYN/ACK → ACK | — | ABERTA |
| Conexão recusada | SYN → RST | `ConnectionRefusedError` | FECHADA |
| Sem resposta no prazo | SYN sem retorno | `TimeoutError` | TIMEOUT |
| Outra condição | ex.: ICMP inalcançável | outro `OSError` (+`errno`) | ERRO |

O código segue as etapas sugeridas: validar parâmetros → tentar conexão → interpretar → apresentar/registrar.
Parâmetros: alvo, portas (`80`, `20-25`, `22,80,8000-8010`), `-t` timeout, `-w` simultaneidade (1–100),
`-o` exportação, `--log`.

**Pseudocódigo** (fluxograma completo em `docs/planejamento.md`):

```text
validar argumentos; resolver alvo uma vez; recusar IP público sem --autorizado
para cada porta p (até N em paralelo):
    tente: socket TCP; settimeout(t); connect(ip, p)  -> ABERTA
    exceto ConnectionRefusedError                     -> FECHADA
    exceto TimeoutError                               -> TIMEOUT   (não é "fechada")
    exceto OSError                                    -> ERRO (errno)
    sempre: fechar o socket; registrar resultado (uma falha não interrompe as demais)
em Ctrl+C: cancelar o que falta e mostrar o parcial
imprimir tabela (alvo, porta, resultado), resumo e duração; opcionalmente gravar JSON/CSV
```

**Por que uma conexão TCP revela a disponibilidade de uma porta?** Porque o handshake obriga o destino a
reagir ao SYN de forma diferente conforme o estado da porta: `LISTEN` → SYN/ACK; sem processo → RST;
filtrada → silêncio. Cada reação é observável sem enviar dados de aplicação.

## 2. Resultados dos testes

Laboratório (`lab/servidor_teste.py`): serviços ativos em 9001 e 9002; 9004 com a fila de conexões saturada
(o kernel descarta os SYNs, simulando firewall `DROP`); 9003 e 9005 sem nada escutando. O `ss -ltn` confirmou
LISTEN em 9001, 9002 e 9004 e ausência de 9003/9005 (`evidencias/01_testes_iniciais.md`).

| Porta | Situação real | Scanner | Tempo |
|---|---|---|---|
| 9001, 9002 | serviço ativo | ABERTA | < 1 ms |
| 9003, 9005 | sem serviço | FECHADA (RST) | < 1 ms |
| 9004 | SYN descartado | TIMEOUT | 1000 ms (= `-t 1`) |

O scanner identificou corretamente todas as portas com serviço e tratou as sem serviço como FECHADA, sem erro.

**Tratamento de erros** (`evidencias/05_tratamento_erros.md`, 12 casos automatizados): porta fora de 1–65535,
porta não numérica, porta 0, intervalo invertido ou malformado, host inexistente, IP público sem autorização e
timeout inválido geram mensagem clara e código de saída 2, **sem `Traceback`**. Timeout numa porta é registrado
e o scan continua. Em Ctrl+C real (SIGINT) o programa exibe os resultados parciais e sai com código 130. Uma
falha numa porta não afeta as outras (`verificar_porta` nunca propaga exceção; há teste automatizado), e o `with`
garante o fechamento do socket. Também há 15 testes unitários (`python -m unittest discover -s tests`).

**Por que timeout ≠ porta fechada?** FECHADA exige uma resposta (RST); timeout é **ausência** de resposta
dentro do prazo, e pode ser firewall com DROP, perda de pacote, host/rede lento ou serviço sobrecarregado. O
experimento abaixo mostra um caso em que a porta estava aberta e o resultado foi TIMEOUT.

| Cenário (`evidencias/04_efeito_timeout.md`) | `-t` | Resultado | Tempo |
|---|---|---|---|
| Porta nunca responde | 0,5 s | TIMEOUT | 500 ms |
| Porta nunca responde | 3 s | TIMEOUT | 3003 ms |
| Serviço volta a atender após 0,4 s | 0,5 s | **TIMEOUT** (porta já aberta!) | 501 ms |
| Serviço volta a atender após 0,4 s | 3 s | **ABERTA** | ≈ 1010 ms |

O SYN inicial foi descartado; o cliente só o retransmite após ~1 s (RTO inicial do TCP). Com `-t 0.5` o
scanner desiste antes da retransmissão e erra a conclusão; com `-t 3` ele a captura.

## 3. Comparação com o Nmap (`nmap -sT -Pn -p 9001-9004 127.0.0.1`)

| Porta TCP | Estado esperado | Scanner desenvolvido | Nmap |
|---|---|---|---|
| 9001 | ABERTA | ABERTA | **[PREENCHER após rodar]** |
| 9002 | ABERTA | ABERTA | **[PREENCHER após rodar]** |
| 9003 | FECHADA | FECHADA | **[PREENCHER após rodar]** |
| 9004 | sem resposta | TIMEOUT | **[PREENCHER após rodar]** |

> **Pendência:** o Nmap não estava instalado na máquina de desenvolvimento. Rodar `python experimentos/comparar_nmap.py`
> após `sudo apt install nmap` — o script gera `evidencias/02_comparacao_nmap.md` com a coluna do Nmap real e
> verifica a equivalência. **Não copiar valores sem executar.** Depois, ajustar o texto abaixo ao que foi observado.

**Análise (previsão a confirmar com a execução):** espera-se concordância em 9001–9003 (`open`/`closed`), pois
`-sT` usa a mesma chamada `connect()` do SO. Em 9004 o Nmap deve reportar `filtered`, que corresponde ao nosso
TIMEOUT: o Nmap faz a mesma inferência (sem resposta ⇒ possivelmente filtrada), mas com **retransmissões e
timeouts adaptativos** baseados no RTT medido. Nosso scanner faz uma tentativa só com timeout fixo — por isso o
experimento acima mostra que ele pode errar onde o Nmap, retentando, acertaria. Outros fatores de divergência:
timeout, retentativas, rate limiting do alvo, condição da rede no momento. Nmap também oferece *service/version
detection* (`-sV`), que o scanner não faz.

**Uma porta aberta indica vulnerabilidade? Não.** Indica apenas que uma conexão TCP foi aceita naquelas
condições. Saber **qual serviço** e **qual versão** exige passos adicionais (banner, fingerprint), e afirmar
uma **vulnerabilidade** exige ainda confrontar a versão/configuração com CVEs ou testes específicos. São três
etapas distintas: porta aberta → serviço identificado → vulnerabilidade confirmada. Na demonstração, a
porta 6379 rotulada `redis` pelo scanner era um serviço falso, mostrando que o nome não prova nada.

## 4. Experimento — mudança de estado do serviço (`evidencias/03_experimento_estado.md`)

Porta 9001; em cada rodada `ss -ltn` confirmou independentemente o estado de escuta.

| Rodada | Ação no serviço | `ss -ltn` | Scanner |
|---|---|---|---|
| A | em execução | LISTEN | ABERTA |
| B | interrompido | ausente | FECHADA (RST) |
| C | reiniciado | LISTEN | ABERTA |

Ao parar o serviço, o socket de escuta deixa de existir e o SO passa a responder RST ao SYN, convertendo
ABERTA em FECHADA sem nenhuma mudança no scanner. Em C o estado volta. Logo, **o resultado de um scan é uma
observação em um instante**, não uma propriedade permanente: serviços sobem, caem e são reconfigurados, e
firewalls mudam regras. Um relatório de scan deve sempre registrar data/hora.

## 5. Melhorias implementadas

Foram implementadas seis (`evidencias/06_melhorias.md`): **concorrência limitada** (`-w`, pool de threads,
teto 100 para não gerar carga excessiva), **exportação JSON/CSV** (`-o`), **medição de desempenho** (duração total
e por porta), **identificação de serviços** (nome da tabela do SO, sinalizado como não confirmatório), **CLI com
argparse** e **log de execução** (`--log`). Ganho medido: 4 portas com timeout de 1 s levaram 4,01 s em modo
sequencial e 1,00 s com `-w 6` (~4×).

## 6. Análise crítica e limitações

1. **Uso de sockets:** `connect()` com `settimeout` provoca o handshake; o desfecho (retorno, `ConnectionRefusedError`,
   `TimeoutError`, outro `OSError`) é mapeado em ABERTA/FECHADA/TIMEOUT/ERRO.
2. **Limitações:** só TCP Connect (sem UDP, sem SYN scan furtivo); handshake completo é **ruidoso** (aparece em logs
   do alvo); uma tentativa por porta e timeout fixo (sem retransmissão nem RTT adaptativo); só o primeiro endereço
   resolvido (IPv4 preferido); não identifica serviço nem versão (o nome é só uma tabela); não detecta filtragem
   com precisão (TIMEOUT é ambíguo); testes em loopback não refletem latência/perda reais; o truque da porta
   saturada é específico do Linux; um Ctrl+C aguarda até `-t` segundos pelas conexões já em curso.
3. **Influência do timeout:** curto demais gera falsos TIMEOUT em portas abertas porém lentas (tabela da seção 2); longo
   demais deixa o scan lento (portas filtradas custam `-t` cada, atenuado pela concorrência). Deve-se calibrar pelo
   RTT da rede e, na dúvida, repetir com `-t` maior.
4. **Diferenças em relação ao Nmap:** ver seção 3 (preencher conforme a execução real).
5. **Mudanças de estado:** o scanner acompanhou corretamente A→B→C, confirmado por `ss`; o resultado vale para o momento da observação.
6. **Melhorias para confiabilidade/eficiência:** retentativas e timeout adaptativo; *banner grabbing* e detecção de
   versão; limitação de taxa (rate limit) configurável; suporte a IPv6 e múltiplos IPs por nome; escaneamento de
   múltiplos alvos; UDP; timestamp em todas as saídas; testes em rede real autorizada com latência.

**Abertura × serviço × vulnerabilidade:** o scanner entrega apenas o 1º degrau (porta aceitou conexão). Identificar
o serviço (2º) e confirmar uma vulnerabilidade (3º) exigem procedimentos adicionais e autorização específica.
