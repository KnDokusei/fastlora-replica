#!/usr/bin/env bash
# Extensión H12: las topologías del Exp. 2 con 4 semillas extra de FLoRa (seed-set 1–4; la 0 es la del Exp. 2).
# 10, 50 y 100 nodos: las 60 topologías. 500 nodos (~20 min por corrida): las topologías R500 × G500, por defecto
# solo la 0 con 1 y 4 GW; todas: R500="0 1 2 3 4" G500="1 2 3 4".
# Uso: scripts/semillas.sh   (WORKERS=4 por defecto; resultados en results/semillas/, reanudable, log en log.txt)
#      SOLO_LISTA=1 scripts/semillas.sh   muestra las corridas pendientes sin correr nada
# Corre con nice 10 (prioridad baja, por si la máquina es compartida) y al final corre scripts/analizar_semillas.py.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKERS="${WORKERS:-4}"
R500="${R500:-0}"
G500="${G500:-1 4}"
mkdir -p "$ROOT/results/semillas"

lista() {
    # las 4 semillas de cada topología seguidas: con 4 workers, cada tanda completa una topología
    for r in $R500; do for g in $G500; do for k in 1 2 3 4; do echo "500 $g $r $k"; done; done; done
    for n in 100 50 10; do for g in 1 2 3 4; do for r in 0 1 2 3 4; do for k in 1 2 3 4; do
        echo "$n $g $r $k"
    done; done; done; done
}
pendientes() {
    lista | while read -r n g r k; do
        [ -f "$ROOT/results/semillas/n${n}_gw${g}_r${r}_s${k}/resumen.csv" ] || echo "$n $g $r $k"
    done
}
TOTAL=$(lista | wc -l)
if [ -n "${SOLO_LISTA:-}" ]; then
    pendientes
    echo "Pendientes: $(pendientes | wc -l) de $TOTAL"
    exit
fi

pendientes | "$ROOT/scripts/sim.sh" xargs -r -P "$WORKERS" -L 1 sh -c \
    'nice -n 10 python scripts/medir_corrida.py $0 $1 $2 --dir results/semillas --semilla-flora $3' \
    2>&1 | tee -a "$ROOT/results/semillas/log.txt" || echo "Alguna corrida falló: revisar results/semillas/log.txt"

echo "Corridas terminadas: $(($TOTAL - $(pendientes | wc -l))) / $TOTAL ($(date))" | tee -a "$ROOT/results/semillas/log.txt"
"$ROOT/scripts/sim.sh" python scripts/analizar_semillas.py 2>&1 | tee "$ROOT/results/semillas/analisis.txt"
