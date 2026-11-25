# Guia da demonstração prática (Roteiro 4, seção 9.4)

O roteiro permite uso de IA, **mas exige que você entenda e consiga explicar/modificar o código**. Este guia
resume o código e prepara as situações que o professor pode pedir.

## 1. Roteiro sugerido (≈ 5 min)

```bash
# terminal A — laboratório
python lab/servidor_teste.py                     # 9001 e 9002 abertas, 9004 = timeout

# terminal B
python portscanner.py 127.0.0.1 -p 9001-9005 -t 1          # ABERTA / FECHADA / TIMEOUT
python portscanner.py 127.0.0.1 -p 9001-9005 -t 0.2        # timeout menor: 9004 volta mais rápido
ss -ltn | grep 900                                          # confirma portas em LISTEN pelo SO
# Ctrl+C no terminal A (serviço interrompido) e repetir o scan -> 9001/9002 viram FECHADA
python lab/servidor_teste.py                                # reinicia -> voltam a ABERTA
python portscanner.py 127.0.0.1 -p 70000                    # erro tratado, sem Traceback
python portscanner.py 127.0.0.1 -p 9001-9004 -o r.json --log r.log
nmap -sT -p 9001-9004 127.0.0.1                             # comparação
```

## 2. O que o professor pode pedir — e onde mexer

| Pedido | Como fazer |
|---|---|
| Alterar porta/intervalo | `-p 8000-8100`, `-p 22,80,443` (função `parse_portas`) |
| Modificar o timeout | `-t 0.3` (vira `sock.settimeout()` em `tentar_conexao`) |
| Parar/iniciar um serviço | Ctrl+C / reiniciar `lab/servidor_teste.py`, ou `python -m http.server 8000` e matar |
| Resultado inesperado | ver §4 (TIMEOUT, ERRO) |
| Explicar uma função | ver §3 |

## 3. O código, função por função (`portscanner.py`)

| Função | O que faz | Ponto para saber explicar |
|---|---|---|
| `parse_portas` | converte `"22,80,8000-8010"` em lista; valida 1–65535, início ≤ fim | usa `set` p/ tirar repetidas; `isascii()+isdigit()` rejeita `²`, `-5`, `1.5` |
| `resolver_alvo` | `getaddrinfo` **uma vez**; devolve (família, IP); prefere IPv4 | evita DNS por porta; `gaierror` → "endereço inválido" |
| `alvo_nao_publico` | `not ip.is_global` | trava ética: público exige `--autorizado` |
| **`tentar_conexao`** | **o coração**: `socket` + `settimeout` + `connect` e `except` | **ordem dos `except`**: `ConnectionRefusedError` e `TimeoutError` são subclasses de `OSError`, então vêm antes |
| `verificar_porta` | chama `tentar_conexao`, mede tempo, monta `ResultadoPorta`, loga | `try/except Exception` evita que uma porta derrube as demais |
| `escanear` | `ThreadPoolExecutor(max_workers=N)`; coleta com `as_completed` | em Ctrl+C: `shutdown(cancel_futures=True)` e mantém o parcial |
| `imprimir_tabela/resumo` | saída alinhada (alvo, porta, resultado...) | rodapé avisa que nome de serviço e TIMEOUT são ambíguos |
| `salvar_resultados` | JSON (com `meta`) ou CSV conforme extensão | |
| `main` | orquestra e define códigos de saída 0/1/2/130 | |

**Como `connect()` vira estado:** `connect()` retorna → handshake feito → `ABERTA`. RST → `ConnectionRefusedError` →
`FECHADA`. Nada volta até `settimeout` expirar → `TimeoutError` → `TIMEOUT`. Qualquer outro `OSError` → `ERRO` (+`errno`).

## 4. Perguntas prováveis (respostas curtas)

- **Por que `with socket.socket()`?** Fecha o socket sempre, mesmo em exceção → não vaza descritores.
- **Por que TIMEOUT não é "fechada"?** Fechada = alguém respondeu RST. Timeout = ninguém respondeu *a tempo*: firewall
  DROP, perda, lentidão. Prova: `experimentos/efeito_timeout.py` (mesma porta aberta, TIMEOUT com 0,5 s, ABERTA com 3 s).
- **Por que o Nmap pode dar resultado diferente?** Retransmite, timeout adaptativo ao RTT, rate limiting, estado do alvo
  no momento. O nosso faz 1 tentativa com timeout fixo.
- **Aberta = vulnerável?** Não: porta aberta → serviço → versão → vulnerabilidade são etapas distintas.
- **Por que o handshake completo é "barulhento"?** O alvo registra a conexão; SYN scan (`-sS`) não completa o handshake.
- **O que `listen(0)` + sem `accept()` faz no lab?** Enche a fila; o kernel Linux descarta SYNs → cliente só vê timeout.
- **Por que `-w` tem teto 100?** Para não gerar carga excessiva (exigência do roteiro).
- **Por que o nome `redis` na 6379 não prova nada?** Vem de `getservbyport` (tabela do SO), não de conversar com o serviço.

## 5. Antes de apresentar

- [ ] `./rodar_tudo.sh` sem falhas (exceto Nmap pendente, se ainda não instalado)
- [ ] Portas 9001–9007 livres na máquina da demonstração (`ss -ltn | grep 900`)
- [ ] Ter lido o código inteiro de `portscanner.py` (~400 linhas, boa parte é comentário e docstring) pelo menos uma vez
