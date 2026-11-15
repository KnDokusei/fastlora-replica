#!/usr/bin/env bash
# Corre experimentos en otra máquina por SSH; siguen corriendo aunque este PC se apague.
# Uso: scripts/remoto.sh ACCIÓN
#   imagen         copia la imagen Docker (docker save | zstd | ssh docker load)
#   subir          copia código, third_party/ y results/variantes/ (rsync; no borra nada en el remoto)
#   lanzar "CMD"   corre CMD en una sesión tmux "fastlora" del remoto, desde la carpeta del proyecto
#   estado         muestra si la sesión sigue viva y el final del log de semillas
#   bajar [DIR]    trae results/DIR del remoto (por defecto semillas)
# Variables: REMOTO (obligatoria, usuario@host), DIR_REMOTO (fastlora, relativo al home remoto)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTO="${REMOTO:?Definir REMOTO=usuario@host}"
DIR_REMOTO="${DIR_REMOTO:-fastlora}"
IMAGE="${IMAGE:-fastlora-flora:omnetpp6.0.3-inet4.4.1}"

case "${1:-}" in
    imagen)
        docker save "$IMAGE" | zstd -T0 -3 | ssh "$REMOTO" 'zstd -d | docker load' ;;
    subir)
        rsync -az --info=stats1 --exclude /.venv/ --exclude /results/ --exclude /.claude/ \
            --exclude /Informe-avance/ --exclude /Presentacion-avance/ --exclude '/*.pdf' \
            "$ROOT/" "$REMOTO:$DIR_REMOTO/"
        ssh "$REMOTO" "mkdir -p $DIR_REMOTO/results"
        rsync -az "$ROOT/results/variantes" "$REMOTO:$DIR_REMOTO/results/" ;;
    lanzar)
        # tmux deja el proceso vivo al cerrar SSH; la sesión se cierra sola cuando CMD termina
        ssh "$REMOTO" "cd $DIR_REMOTO && tmux new-session -d -s fastlora $(printf %q "$2")" ;;
    estado)
        # sin resumen.csv pero con result.out: en curso si la sesión vive; si no, interrumpida (se repite al relanzar)
        ssh "$REMOTO" "cd $DIR_REMOTO && if tmux has-session -t fastlora 2>/dev/null;
                then echo 'Sesión fastlora: corriendo'; e='en curso'; else echo 'Sesión fastlora: terminada'; e=interrumpida; fi;
            echo \"Corridas con resumen.csv: \$(ls results/semillas/*/resumen.csv 2>/dev/null | wc -l)\";
            for d in results/semillas/*/; do
                [ -f \$d/result.out ] && [ ! -f \$d/resumen.csv ] &&
                    echo \"  \$e: \$(basename \$d)  \$(grep -ao '[0-9]*% completed' \$d/result.out | tail -n 1)\";
            done; uptime" ;;
    bajar)
        mkdir -p "$ROOT/results/${2:-semillas}"
        rsync -az "$REMOTO:$DIR_REMOTO/results/${2:-semillas}/" "$ROOT/results/${2:-semillas}/" ;;
    *)
        sed -n 2,9p "$0"; exit 1 ;;
esac
