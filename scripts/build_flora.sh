#!/usr/bin/env bash
# Compila el FLoRa modificado de los autores (MultiAgent-MARLTC/flora/flora) contra INET 4.4.1.
# Se corre dentro del contenedor: scripts/sim.sh scripts/build_flora.sh
set -euo pipefail
FLORA=/work/third_party/MultiAgent-MARLTC/flora/flora
ln -sfn /opt/inet4.4 "$FLORA/../inet4.4"
cd "$FLORA"
make makefiles
make -j"${JOBS:-2}" MODE=release
