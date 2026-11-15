"""Corre una topología del Exp. 2 en FLoRa y en FAST-LoRa, la cronometra y la compara con el CSV de los autores.

Uso (desde Proyecto/):  scripts/sim.sh python scripts/medir_corrida.py N_NODOS N_GW [REP] [--dir results/exp3] [--semilla-flora K]
REP va de 0 a 4 (topología). La semilla de la topología es la de model_verification_full.py: el índice global de la
corrida. --semilla-flora cambia solo el seed-set de OMNeT++ (los autores usan 0) y agrega _s<K> a la carpeta.
Deja en <dir>/n<N>_gw<G>_r<REP>[_s<K>]/: config.ini, result.sca, result.out, nodos.csv (formato del CSV de los autores)
y resumen.csv (tiempos, RAM y diferencia máxima con los autores). scripts/juntar.py arma las tablas.
"""
import argparse
import os
import resource
import sys
from pathlib import Path
from time import perf_counter, time_ns

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
MARLTC_SRC = RAIZ / "third_party/MultiAgent-MARLTC/src"
sys.path.insert(0, str(MARLTC_SRC))
os.chdir(MARLTC_SRC)  # get_repo_path() busca el repo git desde el directorio actual

from flora_ctrl import get_metrics, run_flora_sim  # noqa: E402
from lora_model import LoraModel  # noqa: E402
from model_verification_full import _get_random_network_config  # noqa: E402
from util import get_configuration_params  # noqa: E402

NODOS = np.array([10, 50, 100, 500])
GWS = np.array([1, 2, 3, 4])
REPS = 5


def indice_global(n: int, g: int, rep: int) -> int:
    params = get_configuration_params((NODOS, GWS), REPS)
    filas = np.flatnonzero((params[:, 0] == n) & (params[:, 1] == g))
    return int(filas[rep])


def tiempo_modelo(config) -> tuple[float, LoraModel]:
    # Igual que model_performance.py: construir el modelo y pedir todas las métricas
    t0 = time_ns()
    modelo = LoraModel(*config.as_tuple)
    _ = (modelo.rss_no_flat_fading, modelo.rss, modelo.pdr_gateway, modelo.pdr, modelo.ee)
    return (time_ns() - t0) * 1e-6, modelo


def tabla_nodos(n, g, rep, config, flora_pdr, flora_ee, modelo) -> pd.DataFrame:
    # Mismas columnas y filas (primero los GW) que single_run() de model_verification_full.py
    comun = {"RUN_NO": rep, "NUM_END_DEVICES": n, "NUM_GATEWAYS": g}
    gws = pd.DataFrame({**comun, "GATEWAY": np.arange(g),
                        "POS_X": config.pos_gateway[:, 0], "POS_Y": config.pos_gateway[:, 1]})
    eds = pd.DataFrame({**comun, "END_DEVICE": np.arange(n),
                        "POS_X": config.pos_end_device[:, 0], "POS_Y": config.pos_end_device[:, 1],
                        "SF": config.initial_sf, "TP": config.initial_tp,
                        "flora_PDR": flora_pdr, "flora_EE": flora_ee,
                        "model_PDR": modelo.pdr, "model_EE": modelo.ee})
    return pd.concat([gws, eds], ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int)
    ap.add_argument("g", type=int)
    ap.add_argument("rep", type=int, nargs="?", default=0)
    ap.add_argument("--dir", default="results/exp3")
    ap.add_argument("--semilla-flora", type=int, default=0, help="seed-set de OMNeT++ (0 = la de los autores)")
    a = ap.parse_args()
    n, g, rep, k = a.n, a.g, a.rep, a.semilla_flora
    sufijo = f"_s{k}" if k else ""
    etiqueta = f"[n{n} gw{g} r{rep}{sufijo}]"

    run_no = indice_global(n, g, rep)
    config = _get_random_network_config(n, g, seed=run_no)

    salida = RAIZ / a.dir / f"n{n}_gw{g}_r{rep}{sufijo}"
    salida.mkdir(parents=True, exist_ok=True)
    ini = salida / "config.ini"
    config.to_inifile(ini, simtime_days=5)
    if k:
        with open(ini, "a") as f:  # el template tiene una sola sección, [General], y no termina en salto de línea
            f.write(f"\nseed-set = {k}\n")

    print(f"{etiqueta} semilla de topología {run_no}: corriendo FLoRa...", flush=True)
    t0 = perf_counter()
    _, sca, _ = run_flora_sim(ini, salida, "result")
    t_flora = perf_counter() - t0
    rss_mib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024  # Linux entrega KiB
    flora_pdr, flora_ee = get_metrics(sca)

    tiempo_modelo(_get_random_network_config(1, 1))  # calentamiento: carga imports y cachés
    t_modelo, modelo = tiempo_modelo(config)

    nodos = tabla_nodos(n, g, rep, config, flora_pdr, flora_ee, modelo)
    nodos.to_csv(salida / "nodos.csv", index=False)

    # Comparación nodo a nodo con la misma topología en el CSV de los autores
    aut = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_full.csv", index_col=0)
    aut = aut[(aut.NUM_END_DEVICES == n) & (aut.NUM_GATEWAYS == g) & (aut.RUN_NO == rep)]
    aut = aut[aut.END_DEVICE.notna()].sort_values("END_DEVICE")
    misma_topologia = np.allclose(aut[["POS_X", "POS_Y"]].to_numpy(), config.pos_end_device)
    dif = {
        "flora_PDR": np.abs(flora_pdr - aut.flora_PDR.to_numpy()).max(),
        "flora_EE": np.abs(flora_ee - aut.flora_EE.to_numpy()).max(),
        "model_PDR": np.abs(modelo.pdr - aut.model_PDR.to_numpy()).max(),
        "model_EE": np.abs(modelo.ee - aut.model_EE.to_numpy()).max(),
    }

    print(f"{etiqueta} FLoRa {t_flora:.1f} s, pico de RAM {rss_mib:.0f} MiB | FAST-LoRa {t_modelo:.2f} ms | "
          f"topología igual: {misma_topologia} | máx. dif. con autores {max(dif.values()):.1e}", flush=True)

    pd.DataFrame([{
        "NUM_END_DEVICES": n, "NUM_GATEWAYS": g, "REP": rep, "RUN_NO_GLOBAL": run_no, "SEMILLA_FLORA": k,
        "T_FLORA_S": t_flora, "RSS_FLORA_MIB": rss_mib, "T_MODELO_MS": t_modelo,
        "MISMA_TOPOLOGIA": misma_topologia, **{f"MAXDIF_{c}": v for c, v in dif.items()},
    }]).to_csv(salida / "resumen.csv", index=False)


if __name__ == "__main__":
    main()
