"""Extensión H12: separa el error del modelo del ruido de muestreo de FLoRa promediando semillas.

Uso (desde Proyecto/):  .venv/bin/python scripts/analizar_semillas.py   (o scripts/sim.sh python scripts/analizar_semillas.py)
Semilla 0: CSV de los autores (idéntico a la réplica). Semillas 1–4: results/semillas/ (scripts/semillas.sh).
Variantes: results/variantes/exp2_nodos.csv (scripts/variantes.py). Escribe results/semillas/analisis_*.csv.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
N_PAQ = 432  # 5 días × 86 400 s × 0,001 paq/s
CLAVES = ["NUM_END_DEVICES", "NUM_GATEWAYS", "RUN_NO", "END_DEVICE"]

aut = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_full.csv", index_col=0)
aut = aut[aut.END_DEVICE.notna()].assign(SEMILLA=0)
tablas = [aut[CLAVES + ["SEMILLA", "flora_PDR", "flora_EE"]]]
for f in (RAIZ / "results/semillas").glob("n*_gw*_r*_s*/nodos.csv"):
    k = int(re.search(r"_s(\d+)$", f.parent.name).group(1))
    t = pd.read_csv(f)
    tablas.append(t[t.END_DEVICE.notna()].assign(SEMILLA=k)[CLAVES + ["SEMILLA", "flora_PDR", "flora_EE"]])
flora = pd.concat(tablas, ignore_index=True)

# Solo las topologías que tienen las 5 semillas
n_sem = flora.groupby(CLAVES[:3]).SEMILLA.nunique()
completas = n_sem[n_sem == 5].index
flora = flora.set_index(CLAVES[:3]).loc[completas].reset_index()
print(f"Topologías con 5 semillas: {len(completas)}")

var = pd.read_csv(RAIZ / "results/variantes/exp2_nodos.csv")
variantes = [c[:-4] for c in var.columns if c.endswith("_PDR") and c not in ("flora_PDR", "model_PDR")]
var = var.set_index(CLAVES)[[f"{v}_{m}" for v in variantes for m in ("PDR", "EE")]]  # sin flora_*/model_*


def piso(p, r):
    p = np.clip(p, 0, 1)
    return (np.sqrt(2 / np.pi) * np.sqrt(p * (1 - p) / (N_PAQ * r))).mean()


# MAE contra el número de semillas promediadas (modelo base)
filas = []
for r in range(1, 6):
    prom = flora[flora.SEMILLA < r].groupby(CLAVES)[["flora_PDR", "flora_EE"]].mean()
    m = prom.join(var[["base_PDR", "base_EE"]], how="inner")
    for (n, g), grp in m.groupby(level=[0, 1]):
        filas.append({"R": r, "NUM_END_DEVICES": n, "NUM_GATEWAYS": g,
                      "MAE_PDR": (grp.flora_PDR - grp.base_PDR).abs().mean(),
                      "SESGO_PDR": (grp.flora_PDR - grp.base_PDR).mean(),
                      "PISO_PDR": piso(grp.base_PDR, r),
                      "MAE_EE": (grp.flora_EE - grp.base_EE).abs().mean()})
por_r = pd.DataFrame(filas)
por_r.to_csv(RAIZ / "results/semillas/analisis_por_semillas.csv", index=False)

print("\nMAE PDR (×10⁻²) del modelo base contra el promedio de R semillas de FLoRa, y piso binomial")
for n, grp in por_r.groupby("NUM_END_DEVICES"):
    t = grp.groupby("R")[["MAE_PDR", "PISO_PDR", "SESGO_PDR"]].mean() * 100
    print(f"\n{n} nodos (promedio sobre GW):")
    print(t.round(3).to_string())

# Variantes contra el promedio de las 5 semillas
prom5 = flora.groupby(CLAVES)[["flora_PDR", "flora_EE"]].mean().join(var, how="inner")
res = pd.DataFrame([{"VARIANTE": v,
                     "MAE_PDR_R1": None, "MAE_PDR_R5": (prom5.flora_PDR - prom5[f"{v}_PDR"]).abs().mean(),
                     "SESGO_PDR_R5": (prom5.flora_PDR - prom5[f"{v}_PDR"]).mean(),
                     "MAE_EE_R5": (prom5.flora_EE - prom5[f"{v}_EE"]).abs().mean()} for v in variantes])
s0 = flora[flora.SEMILLA == 0].set_index(CLAVES).join(var, how="inner")
res["MAE_PDR_R1"] = [(s0.flora_PDR - s0[f"{v}_PDR"]).abs().mean() for v in variantes]
res.insert(4, "MAE_EE_R1", [(s0.flora_EE - s0[f"{v}_EE"]).abs().mean() for v in variantes])
res["PISO_R5"] = piso(prom5.base_PDR, 5)
res.to_csv(RAIZ / "results/semillas/analisis_variantes.csv", index=False)
print("\nVariantes en las mismas topologías: MAE PDR con 1 y con 5 semillas (×10⁻²), MAE EE (bits/mJ)")
print(res.to_string(index=False, formatters={c: (lambda x: f"{x * 100:.3f}") for c in
                                              ["MAE_PDR_R1", "MAE_PDR_R5", "SESGO_PDR_R5", "PISO_R5"]}
                    | {c: "{:.4f}".format for c in ["MAE_EE_R1", "MAE_EE_R5"]}))

# Por tamaño de red, con 5 semillas: si el modelo solo tuviera ruido de FLoRa, ~4,6 % de los nodos tendría |z| > 2
filas = []
for v in variantes:
    p = prom5[f"{v}_PDR"]
    err = prom5.flora_PDR - p
    q = p.clip(1e-6, 1 - 1e-6)
    z = err / np.sqrt(q * (1 - q) / (N_PAQ * 5))
    interior = (p > 0.001) & (p < 0.999)  # con PDR ≈ 0 o 1 la binomial no tiene varianza
    for n in prom5.index.unique(level=0):
        en_n = prom5.index.get_level_values(0) == n
        filas.append({"VARIANTE": v, "NUM_END_DEVICES": n,
                      "TOPOLOGIAS": prom5[en_n].index.droplevel(3).nunique(), "NODOS": en_n.sum(),
                      "MAE_PDR": err[en_n].abs().mean(), "SESGO_PDR": err[en_n].mean(),
                      "PISO_PDR": piso(q[en_n], 5), "Z_MAYOR_2": (z[en_n & interior].abs() > 2).mean()})
por_tam = pd.DataFrame(filas)
por_tam.to_csv(RAIZ / "results/semillas/analisis_variantes_por_tamano.csv", index=False)
print("\nPor tamaño, con 5 semillas: MAE / sesgo PDR (×10⁻²) / % de nodos con |z| > 2")
celda = por_tam.assign(T=por_tam.apply(lambda r: f"{r.MAE_PDR * 100:.3f} / {r.SESGO_PDR * 100:+.3f} / "
                                                  f"{r.Z_MAYOR_2 * 100:.1f} %", axis=1))
print(celda.pivot(index="VARIANTE", columns="NUM_END_DEVICES", values="T").loc[variantes].to_string())
print("Topologías por tamaño:", por_tam.drop_duplicates("NUM_END_DEVICES").set_index("NUM_END_DEVICES").TOPOLOGIAS.to_dict())
