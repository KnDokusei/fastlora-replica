#!/usr/bin/env bash
# Clona las dependencias externas en third_party/ en los commits fijados en .claude/decisiones.md.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third_party

clone() {  # url carpeta commit
    [ -d "third_party/$2/.git" ] || git clone --quiet "$1" "third_party/$2"
    git -C "third_party/$2" checkout --quiet "$3"
}

clone https://github.com/jaznrp/FastLoRa.git          FastLoRa          fb8b1bea7204d0c03d3cf28cd5977242692ee44a
clone https://github.com/jaznrp/MultiAgent-MARLTC.git MultiAgent-MARLTC 2f623b74458307d446908d11e33ec916539f9382
clone https://github.com/florasim/flora.git           flora             v1.1.0   # oficial, solo para comparar

# MARLTC espera INET en flora/inet4.4; dentro del contenedor INET vive en /opt/inet4.4
ln -sfn /opt/inet4.4 third_party/MultiAgent-MARLTC/flora/inet4.4

# Resultados de validación de los autores: publicados en d72e7ad y borrados en 2f623b7.
# Quedan en third_party/ (no se versionan: MARLTC no declara licencia).
mkdir -p third_party/resultados_autores
for f in model_verification_simple.csv model_verification_full.csv test.out; do
    git -C third_party/MultiAgent-MARLTC show "d72e7ad:src/result/$f" > "third_party/resultados_autores/$f"
done
