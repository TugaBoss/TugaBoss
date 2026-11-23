#!/bin/bash
cd "$(dirname "$0")/.."
for r in 01-pagina 02-viral 03-site 04-claude 05-cerebros; do
  echo "== $r"; python3 _motor/build.py lote-01/$r 2>&1 | grep -E 'duração|ok |ERRO|Error|Traceback'
done
