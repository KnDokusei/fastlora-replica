#!/usr/bin/env bash
# Exp. 2 completo: 4 tamaños × 4 GW × 5 topologías = 80 corridas de FLoRa + FAST-LoRa en un solo contenedor.
# Uso: scripts/exp2.sh   (WORKERS=4 por defecto, uno por núcleo físico; resultados en results/exp2/)
# Reanudable: salta las corridas que ya tienen resumen.csv. Log en results/exp2/log.txt.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKERS="${WORKERS:-4}"
mkdir -p "$ROOT/results/exp2"

# Las de 500 nodos primero: son el 95 % del tiempo y así ningún worker queda solo al final con una larga.
"$ROOT/scripts/sim.sh" bash -c '
for n in 500 100 50 10; do for g in 1 2 3 4; do for r in 0 1 2 3 4; do
    [ -f results/exp2/n${n}_gw${g}_r${r}/resumen.csv ] || echo "$n $g $r"
done; done; done |
xargs -P '"$WORKERS"' -L 1 sh -c "python scripts/medir_corrida.py \$0 \$1 \$2 --dir results/exp2"
' 2>&1 | tee -a "$ROOT/results/exp2/log.txt" || echo "Alguna corrida falló: revisar results/exp2/log.txt"

"$ROOT/.venv/bin/python" "$ROOT/scripts/juntar.py" results/exp2 | tee "$ROOT/results/exp2/resumen.txt"
