#!/usr/bin/env bash
# Ejecuta un comando en el contenedor de simulación con el proyecto montado en /work.
# Uso: scripts/sim.sh [comando ...]   (sin argumentos abre una shell)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TTY=()
[ -t 0 ] && [ -t 1 ] && TTY=(-t)
# La imagen corre como sim (UID 1000). En una máquina con otro UID, el contenedor no podría escribir en /work.
USR=()
[ "$(id -u)" = "${SIM_UID:-1000}" ] || USR=(--user "$(id -u):$(id -g)" -e HOME=/tmp)
exec docker run --rm -i "${TTY[@]}" "${USR[@]}" -v "$ROOT":/work -w "${SIM_WORKDIR:-/work}" \
    "${IMAGE:-fastlora-flora:omnetpp6.0.3-inet4.4.1}" "${@:-bash}"
