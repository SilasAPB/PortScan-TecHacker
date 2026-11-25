#!/usr/bin/env bash
# Reexecuta testes + todos os experimentos e regenera a pasta evidencias/.
# Uso: ./rodar_tudo.sh
cd "$(dirname "$0")" || exit 1
PY="${PYTHON:-python3}"
falhou=0

passo() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
roda()  { "$@" >/dev/null 2>&1 && echo "   OK" || { echo "   FALHOU (código $?)"; falhou=1; }; }

passo "Testes unitários";                         "$PY" -m unittest discover -s tests 2>&1 | tail -3
passo "3.3 Testes iniciais";                      roda "$PY" experimentos/testes_iniciais.py
passo "4   Tratamento de erros (7 situações)";    roda "$PY" experimentos/tratamento_erros.py
passo "5   Comparação com Nmap";
"$PY" experimentos/comparar_nmap.py >/dev/null 2>&1; c=$?
[ $c -eq 0 ] && echo "   OK" || { [ $c -eq 3 ] && echo "   PENDENTE: nmap não instalado (sudo apt install nmap)" || { echo "   FALHOU"; falhou=1; }; }
passo "6   Mudança de estado do serviço (A/B/C)"; roda "$PY" experimentos/estado_servico.py
passo "4/8 Efeito do timeout";                    roda "$PY" experimentos/efeito_timeout.py
passo "7   Melhorias";                            roda "$PY" experimentos/demo_melhorias.py

echo; echo "Evidências em: $(pwd)/evidencias/"
exit $falhou
