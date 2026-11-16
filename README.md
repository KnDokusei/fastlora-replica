# Replicación de FAST-LoRa

Réplica independiente de la validación de FAST-LoRa (Acosta-García et al., *IEEE Access* vol. 14, 2026):
modelo analítico contra simulación paquete a paquete en FLoRa. Proyecto del curso IPD-438, USM.

## Resultados

El informe final está en [`Informe-final/informe_final.pdf`](Informe-final/informe_final.pdf) (6 páginas). En resumen:

- El entorno reproduce de forma exacta los resultados de los autores: las 144 configuraciones del Exp. 1 y las 80 redes del Exp. 2 dan las mismas cifras, y las Tablas 6 y 7 del artículo coinciden celda por celda.
- Con una sola corrida de FLoRa, el 88 % del MAE de la PDR que reporta el artículo (0,940×10⁻²) se explica por el azar de muestreo del simulador. Promediando cinco corridas por red, en redes de hasta 100 nodos el error del modelo queda en el piso de ruido (entre 0,36 y 0,37×10⁻²); con 500 nodos el modelo subestima la PDR en 0,2 a 0,5×10⁻².
- El error de la EE viene sobre todo de que FAST-LoRa y FLoRa usan otro tiempo en el aire y otra potencia de transmisión: con los parámetros de FLoRa y cinco corridas, el MAE baja de 0,040 a 0,009 bits/mJ.
- La aceleración medida es de 1,5 a 3,3×10⁴, un orden de magnitud más que los 10³ que menciona el texto del artículo.

## Entorno

| Dónde | Qué | Para qué |
|---|---|---|
| Host, `.venv` (Python 3.12) | FAST-LoRa (`jaznrp/FastLoRa`), numpy 2.2, scipy 1.14, pandas 2.2, matplotlib | Modelo analítico, análisis y figuras |
| Docker `fastlora-flora:omnetpp6.0.3-inet4.4.1` | Ubuntu 22.04, OMNeT++ 6.0.3, INET 4.4.1, Python 3.10 con los requisitos de MARLTC | FLoRa 1.1.0 modificado por los autores y sus scripts de validación |

```bash
scripts/setup_third_party.sh        # clona FastLoRa, MultiAgent-MARLTC y FLoRa en los commits fijados
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/build_image.sh              # OMNeT++ + INET; JOBS=2 por defecto (~1 h)
scripts/sim.sh scripts/build_flora.sh   # compila FLoRa dentro del contenedor
scripts/sim.sh                      # shell en el contenedor, proyecto montado en /work
```

Los repositorios de los autores no declaran las versiones de OMNeT++ ni de INET; se eligieron por compatibilidad y se validaron porque la salida coincide con los datos de los autores (sección IV-C del informe). Los commits de cada dependencia están fijados en `scripts/setup_third_party.sh`.

## Experimentos

Todo se corre desde la raíz del repositorio. Los resultados quedan en `results/`; solo se versionan los resúmenes que respaldan las tablas y figuras del informe, y las salidas crudas de OMNeT++ se regeneran con los scripts.

| Qué | Comando | Duración aprox. (i5-1135G7) |
|---|---|---|
| Exp. 1: 1 nodo, 144 configuraciones (script de los autores) | `SIM_WORKDIR=/work/third_party/MultiAgent-MARLTC/src scripts/sim.sh python model_verification_simple.py` | 4 min |
| Una topología del Exp. 2, con tiempos y comparación con los autores | `scripts/sim.sh python scripts/medir_corrida.py 500 1 0` | 19 min (500 nodos) |
| Exp. 2: 80 topologías, 4 en paralelo | `scripts/exp2.sh` | ~2 h |
| Tablas 6 y 7 y criterio de éxito | `.venv/bin/python scripts/juntar.py results/exp2` | segundos |
| Exp. 3: tiempos con la grilla de la Fig. 6, en serie | `scripts/sim.sh python scripts/exp3.py` | ~1 h |
| Informe final (6 páginas, IEEE) | `.venv/bin/python Informe-final/generar_datos.py` y luego `latexmk -pdf informe_final.tex` en `Informe-final/` (usa `Figuras/fig6.pdf`) | segundos |
| Figura de la Fig. 6: artículo contra réplica | `.venv/bin/python scripts/fig6.py` y luego `latexmk -pdf fig6.tex` en `Figuras/` | segundos |
| Variantes del modelo, una por discrepancia | `scripts/sim.sh python scripts/variantes.py` | 15 s |
| Semillas extra de FLoRa (ruido de muestreo) | `scripts/semillas.sh` y luego `.venv/bin/python scripts/analizar_semillas.py` | ~1 h |

El Exp. 1 escribe en `third_party/MultiAgent-MARLTC/src/result/`; se copia a `results/exp1/`.
`exp2.sh` y `semillas.sh` se pueden reanudar: saltan las corridas que ya tienen `resumen.csv`. Para detenerlos: `docker stop $(docker ps -q --filter ancestor=fastlora-flora:omnetpp6.0.3-inet4.4.1)`.
`semillas.sh` corre con `nice 10` y al final llama a `analizar_semillas.py` dentro del contenedor (salida en `results/semillas/analisis.txt`).
Por defecto incluye solo 2 topologías de 500 nodos; el informe usa las 20. Para incluirlas todas: `R500="0 1 2 3 4" G500="1 2 3 4" scripts/semillas.sh` (72 corridas más, ~6 h con 4 workers).
`SOLO_LISTA=1 scripts/semillas.sh` muestra lo que falta sin correr nada.

## Correr en otra máquina

`scripts/remoto.sh` deja una tanda corriendo en otra máquina por SSH, dentro de una sesión tmux, así que sigue aunque este PC se apague.
La máquina se indica con `REMOTO=usuario@host` (obligatoria) y la carpeta con `DIR_REMOTO` (por defecto `fastlora`). El remoto necesita Docker, tmux, rsync y zstd.
Si la máquina está detrás de una VPN, basta con que esté activa durante cada comando: lo que se lanzó sigue corriendo al desconectarse.

| Paso | Comando | Equivalente a mano |
|---|---|---|
| Copiar la imagen (una vez, ~2 min) | `scripts/remoto.sh imagen` | `docker save IMAGEN \| zstd -T0 -3 \| ssh REMOTO 'zstd -d \| docker load'` |
| Copiar el código | `scripts/remoto.sh subir` | `rsync -az --exclude /results/ ... ./ REMOTO:fastlora/` |
| Lanzar | `scripts/remoto.sh lanzar scripts/semillas.sh` | `ssh REMOTO "cd fastlora && tmux new-session -d -s fastlora scripts/semillas.sh"` |
| Ver avance | `scripts/remoto.sh estado` | `ssh -t REMOTO tmux attach -t fastlora` (salir sin cortar: Ctrl-b d) |
| Traer resultados | `scripts/remoto.sh bajar` | `rsync -az REMOTO:fastlora/results/semillas/ results/semillas/` |

Si el UID del remoto no es 1000 (el usuario `sim` de la imagen), `sim.sh` corre el contenedor con el UID del host para poder escribir en `/work`.

## Licencia

El código propio está bajo licencia MIT (ver `LICENSE`). Las imágenes `Presentacion-avance/figs/paper_fig*.png` son figuras de Acosta-García et al., publicadas en *IEEE Access* bajo licencia CC BY 4.0. Los repositorios de los autores se clonan aparte con `scripts/setup_third_party.sh` y conservan sus propias condiciones.
