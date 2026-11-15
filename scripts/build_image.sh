#!/usr/bin/env bash
# Construye la imagen de simulación. JOBS controla los hilos de compilación (por defecto 2, por la RAM disponible).
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -t "${IMAGE:-fastlora-flora:omnetpp6.0.3-inet4.4.1}" \
    --build-arg UID="$(id -u)" --build-arg GID="$(id -g)" --build-arg JOBS="${JOBS:-2}" \
    docker/
