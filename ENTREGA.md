# Mapa da entrega — o que o Roteiro 4 pede × o que foi feito

Legenda: ✅ feito e verificado · 🟡 feito, falta ação sua · ⬜ ação sua

## Entregáveis (seção 9)

| Entregável | Status | Onde |
|---|---|---|
| 9.1 Código-fonte (com melhoria) | ✅ | [`portscanner.py`](portscanner.py), [`lab/`](lab/) |
| 9.2 README | ✅ | [`README.md`](README.md) |
| 9.3 Relatório técnico (2–3 páginas) | 🟡 | [`relatorio/relatorio.md`](relatorio/relatorio.md) — falta nome e a coluna do Nmap |
| 9.4 Demonstração prática | ⬜ | preparar com [`docs/guia_demonstracao.md`](docs/guia_demonstracao.md) |

## Passo a passo do roteiro

| Seção | Pede | Status | Onde está |
|---|---|---|---|
| 1 | Python 3, sockets, sem lib de scan, sem Nmap interno, só alvos autorizados | ✅ | só stdlib; alvos = `127.0.0.1`; trava `--autorizado` para IP público |
| 2 | Planejamento: estratégia, recursos do `socket`, fluxograma/pseudocódigo, questão de análise | ✅ | [`docs/planejamento.md`](docs/planejamento.md) |
| 3.1 | 7 funcionalidades obrigatórias | ✅ | alvo IP/host · porta/intervalo · conexão TCP · lista abertas · diferencia recusada/timeout/erro · `-t` · tabela com alvo, porta, resultado |
| 3.2 | Código organizado em etapas | ✅ | funções separadas por etapa em `portscanner.py` |
| 3.3 | Testes iniciais + `ss` + questão de análise | ✅ | [`evidencias/01_testes_iniciais.md`](evidencias/01_testes_iniciais.md) |
| 4 | Tratamento de 7 situações; não encerrar inesperadamente; fechar sockets | ✅ | [`evidencias/05_tratamento_erros.md`](evidencias/05_tratamento_erros.md) · `tests/` |
| 4 | Questão: por que timeout ≠ fechada | ✅ | relatório §2 · [`evidencias/04_efeito_timeout.md`](evidencias/04_efeito_timeout.md) (prova prática) |
| 5 | Comparação com `nmap -sT`, tabela, divergências, 4 questões | 🟡 | script e tabela prontos; **Nmap não instalado aqui** → rode `experimentos/comparar_nmap.py` e preencha relatório §3 |
| 6 | 3 rodadas A/B/C + questão de análise | ✅ | [`evidencias/03_experimento_estado.md`](evidencias/03_experimento_estado.md) |
| 7 | ≥ 1 melhoria demonstrada e documentada | ✅ | 6 melhorias: [`evidencias/06_melhorias.md`](evidencias/06_melhorias.md) |
| 8 | Análise crítica (6 itens + aberta × serviço × vulnerabilidade) | ✅ | relatório §6 (item 4 depende do Nmap) |
| 10 | Critérios de avaliação (10 pts) | — | mapeados abaixo |

## Critérios de avaliação × evidência

| Critério | Pts | Evidência |
|---|---|---|
| Funcionamento básico do scanner TCP | 3,0 | `portscanner.py`, `01_testes_iniciais.md`, `tests/` |
| Tratamento de erros e parâmetros | 1,5 | `05_tratamento_erros.md` |
| Validação e comparação com Nmap | 1,5 | `02_comparacao_nmap.md` 🟡 |
| Experimento de mudança de estado | 1,0 | `03_experimento_estado.md` |
| Melhoria adicional | 1,0 | `06_melhorias.md` |
| Análise técnica e documentação | 1,0 | `relatorio/`, `README.md`, `docs/` |
| Demonstração e domínio do código | 1,0 | `docs/guia_demonstracao.md` |

## O que falta fazer (ações suas)

1. ⬜ **Instalar o Nmap e rodar a comparação** — `sudo apt install nmap` → `python experimentos/comparar_nmap.py`.
   Depois copiar a coluna "Nmap" para o relatório §3 e **ajustar o parágrafo de análise ao que foi observado**
   (hoje ele é uma previsão, marcada como tal).
2. ⬜ Colocar **nome e data** no relatório e exportar para PDF (o roteiro pede 2–3 páginas; confira o tamanho final).
3. ⬜ **Ler o código** e ensaiar a demonstração (`docs/guia_demonstracao.md`) — o roteiro exige domínio do código.
4. ⬜ Criar o repositório **privado** no GitHub e subir esta pasta (o `.gitignore` já está pronto).

## Como regenerar as evidências

```bash
./rodar_tudo.sh        # testes + todos os experimentos; reescreve evidencias/
```
