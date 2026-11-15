"""Datos para las figuras y tablas del informe de avance.

Uso (desde Proyecto/):  .venv/bin/python Informe-avance/generar_datos.py
Lee los CSV de los autores (third_party/resultados_autores) y la réplica propia del Exp. 1
(results/exp1/model_verification_simple.csv). Escribe Informe-avance/datos/*.dat.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "Informe-avance" / "datos"
SALIDA.mkdir(exist_ok=True)

autores = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_simple.csv", index_col=0)
propio = pd.read_csv(RAIZ / "results/exp1/model_verification_simple.csv", index_col=0)
claves = ["DIST", "SF", "TP"]
m = propio.merge(autores, on=claves, suffixes=("", "_aut"))
assert len(m) == 144

# Réplica contra autores: diferencia máxima por columna
for c in ["flora_pdr", "flora_ee", "model_pdr", "model_ee"]:
    print(f"max |propio - autores| {c}: {np.abs(m[c] - m[c + '_aut']).max():.3e}")

err_pdr = m.flora_pdr - m.model_pdr
err_ee = m.flora_ee - m.model_ee
print(f"Exp1 MAE PDR = {err_pdr.abs().mean():.5f}  SDE = {err_pdr.std():.5f}")
print(f"Exp1 MAE EE  = {err_ee.abs().mean():.4f}  SDE = {err_ee.std():.4f}")
for d, g in m.groupby("DIST"):
    print(f"  d={d} m: MAE PDR = {(g.flora_pdr - g.model_pdr).abs().mean():.5f}, "
          f"MAE EE = {(g.flora_ee - g.model_ee).abs().mean():.4f}")

# Fig. 1: PDR contra potencia a 100 m
for sf in [7, 8, 10, 12]:
    g = m[(m.DIST == 100) & (m.SF == sf)].sort_values("TP")
    g[["TP", "flora_pdr", "model_pdr"]].to_csv(SALIDA / f"pdr_100m_sf{sf}.dat", sep=" ", index=False)

# Fig. 2: error contra PDR del modelo, con el error estándar binomial de FLoRa
N_PAQ = 5 * 86400 * 0.001  # 432 paquetes por nodo en 5 días
m.assign(err=err_pdr)[["model_pdr", "err", "DIST"]].to_csv(SALIDA / "error_pdr.dat", sep=" ", index=False)
p = np.linspace(0, 1, 101)
pd.DataFrame({"p": p, "se2": 2 * np.sqrt(p * (1 - p) / N_PAQ)}).to_csv(SALIDA / "banda.dat", sep=" ", index=False)
dentro = (err_pdr.abs() <= 2 * np.sqrt(m.model_pdr * (1 - m.model_pdr) / N_PAQ) + 1e-12).mean()
print(f"fracción de configuraciones con |error| <= 2 SE: {dentro:.3f}")

# Configuraciones con el mismo margen p - eta dan exactamente la misma PDR en FLoRa
sens = {7: -124, 8: -127, 9: -130, 10: -133, 11: -135, 12: -137}
m["margen"] = m.TP - m.SF.map(sens)
rep = m.groupby(["DIST", "margen"]).flora_pdr.agg(["count", "nunique"])
rep = rep[rep["count"] > 1]
print(f"grupos con igual margen: {len(rep)}, todos con una sola PDR: {(rep['nunique'] == 1).all()}")

# Tabla: Exp. 2 de los autores, MAE por (N, K)
full = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_full.csv", index_col=0)
nodos = full[full.END_DEVICE.notna()]
t = nodos.groupby(["NUM_END_DEVICES", "NUM_GATEWAYS"]).apply(
    lambda g: pd.Series({"pdr": (g.flora_PDR - g.model_PDR).abs().mean() * 100,
                         "ee": (g.flora_EE - g.model_EE).abs().mean()}), include_groups=False)
print(t.unstack().round(3))
print(f"Exp2 por nodo: MAE PDR = {(nodos.flora_PDR - nodos.model_PDR).abs().mean() * 100:.3f}e-2, "
      f"MAE EE = {(nodos.flora_EE - nodos.model_EE).abs().mean():.4f}")
print(f"Exp2 por tabla: MAE PDR = {t.pdr.mean():.3f}e-2, MAE EE = {t.ee.mean():.4f}")
