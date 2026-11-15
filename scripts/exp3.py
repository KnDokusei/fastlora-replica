"""Exp. 3: tiempo de ejecución de FLoRa y FAST-LoRa con la grilla de la Fig. 6 (10–200 nodos, 1–5 GW).

Uso (desde Proyecto/, sin otras simulaciones corriendo):  scripts/sim.sh python scripts/exp3.py
Corre en serie para no contaminar los tiempos (D15). Topologías del generador del Exp. 2 (uniforme en 1×1 km) con
semillas propias (1000 + índice). Reanudable: agrega una fila por corrida a results/exp3_fig6/tiempos.csv y salta
las que ya están. Al final imprime la tabla de la Fig. 6 (promedio sobre GW y repeticiones).
"""
import os
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

NODOS = [10, 20, 50, 100, 200]
GWS = [1, 2, 3, 4, 5]
REPS = 3
REPS_MODELO = 20
SALIDA = RAIZ / "results/exp3_fig6"
TABLA = SALIDA / "tiempos.csv"


def ejecutar_modelo(config) -> LoraModel:
    # Igual que model_performance.py: construir el modelo y pedir todas las métricas
    modelo = LoraModel(*config.as_tuple)
    _ = (modelo.rss_no_flat_fading, modelo.rss, modelo.pdr_gateway, modelo.pdr, modelo.ee)
    return modelo


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    hechas = set()
    if TABLA.exists():
        hechas = set(pd.read_csv(TABLA)[["NUM_END_DEVICES", "NUM_GATEWAYS", "REP"]].itertuples(index=False, name=None))

    ejecutar_modelo(_get_random_network_config(1, 1))  # calentamiento: carga imports y cachés

    # Repetición por fuera: tras la primera pasada (~20 min) ya hay una grilla completa
    grilla = [(n, g, r) for r in range(REPS) for g in GWS for n in NODOS]
    for idx, (n, g, rep) in enumerate(grilla):
        if (n, g, rep) in hechas:
            continue
        config = _get_random_network_config(n, g, seed=1000 + idx)
        carpeta = SALIDA / f"n{n}_gw{g}_r{rep}"
        carpeta.mkdir(exist_ok=True)
        ini = carpeta / "config.ini"
        config.to_inifile(ini, simtime_days=5)

        t0 = perf_counter()
        _, sca, _ = run_flora_sim(ini, carpeta, "result")
        t_flora = perf_counter() - t0
        flora_pdr, flora_ee = get_metrics(sca)

        t_modelo = []
        for _ in range(REPS_MODELO):
            t1 = time_ns()
            modelo = ejecutar_modelo(config)
            t_modelo.append((time_ns() - t1) * 1e-6)

        fila = {"NUM_END_DEVICES": n, "NUM_GATEWAYS": g, "REP": rep, "SEMILLA": 1000 + idx,
                "T_FLORA_S": t_flora, "T_MODELO_MS": np.mean(t_modelo), "T_MODELO_MS_STD": np.std(t_modelo),
                "MAE_PDR": np.abs(flora_pdr - modelo.pdr).mean(), "MAE_EE": np.abs(flora_ee - modelo.ee).mean()}
        pd.DataFrame([fila]).to_csv(TABLA, mode="a", header=not TABLA.exists(), index=False)
        print(f"[n{n} gw{g} r{rep}] FLoRa {t_flora:.1f} s | FAST-LoRa {fila['T_MODELO_MS']:.2f} ms", flush=True)

    t = pd.read_csv(TABLA)
    resumen = t.groupby("NUM_END_DEVICES").agg(
        flora_s=("T_FLORA_S", "mean"), flora_s_std=("T_FLORA_S", "std"),
        modelo_ms=("T_MODELO_MS", "mean"), modelo_ms_std=("T_MODELO_MS", "std"))
    resumen["aceleracion"] = resumen.flora_s / (resumen.modelo_ms * 1e-3)
    print("\nFig. 6 (promedio sobre 1–5 GW y repeticiones):")
    print(resumen.to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main()
