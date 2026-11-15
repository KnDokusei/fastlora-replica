"""Datos para las figuras del informe final.

Uso (desde Proyecto/):  .venv/bin/python Informe-final/generar_datos.py
Lee results/semillas/analisis_por_semillas.csv (scripts/analizar_semillas.py) y escribe Informe-final/datos/*.dat.
La figura de tiempos es Figuras/fig6.pdf (scripts/fig6.py).
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "Informe-final" / "datos"
SALIDA.mkdir(exist_ok=True)

# MAE de la PDR contra el número R de corridas de FLoRa promediadas, por tamaño de red (promedio sobre 1–4 GW)
r = pd.read_csv(RAIZ / "results/semillas/analisis_por_semillas.csv")
t = r.groupby(["R", "NUM_END_DEVICES"])[["MAE_PDR", "PISO_PDR"]].mean().mul(100).unstack()
salida = pd.DataFrame({f"mae{n}": t["MAE_PDR"][n] for n in t["MAE_PDR"].columns})
salida["piso_min"] = t["PISO_PDR"].min(axis=1)
salida["piso_max"] = t["PISO_PDR"].max(axis=1)
salida.to_csv(SALIDA / "mae_r.dat", sep=" ", float_format="%.4f")
print(salida.round(3).to_string())

# Exp. 1: error de la PDR contra la PDR del modelo, con la banda de ±2 desviaciones del ruido de FLoRa
N_PAQ = 432  # 5 días × 86 400 s × 0,001 paq/s
e1 = pd.read_csv(RAIZ / "results/exp1/model_verification_simple.csv", index_col=0)
e1 = e1.assign(err=e1.flora_pdr - e1.model_pdr)
e1[["model_pdr", "err", "DIST"]].to_csv(SALIDA / "error_pdr.dat", sep=" ", index=False)
p = np.linspace(0, 1, 101)
pd.DataFrame({"p": p, "se2": 2 * np.sqrt(p * (1 - p) / N_PAQ)}).to_csv(SALIDA / "banda.dat", sep=" ", index=False)
z = e1.err / np.sqrt((e1.model_pdr * (1 - e1.model_pdr)).clip(lower=1e-12) / N_PAQ)
print(f"Exp. 1: {len(e1)} configuraciones, máx |z| = {z[e1.err.abs() > 1e-9].abs().max():.2f}")
