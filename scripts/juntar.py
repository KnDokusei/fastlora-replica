"""Junta las corridas de scripts/medir_corrida.py y las compara con los autores.

Uso (desde Proyecto/):  .venv/bin/python scripts/juntar.py results/exp2
Escribe <dir>/tiempos.csv y <dir>/model_verification_full.csv (mismo formato y orden que el de los autores).
Si están las 80 corridas, imprime la Tabla 6 (PDR) y la Tabla 7 (EE) y revisa el criterio D12.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
MAE_PDR_MAX, MAE_EE_MAX = 2e-2, 0.08  # D12

d = RAIZ / sys.argv[1]
resumen = pd.concat([pd.read_csv(f) for f in d.glob("n*_gw*_r*/resumen.csv")], ignore_index=True)
resumen = resumen.sort_values("RUN_NO_GLOBAL", ignore_index=True)
resumen.to_csv(d / "tiempos.csv", index=False)

semilla = resumen.get("SEMILLA_FLORA", pd.Series(0, index=resumen.index)).fillna(0).astype(int)
carpetas = [d / (f"n{r.NUM_END_DEVICES}_gw{r.NUM_GATEWAYS}_r{r.REP}" + (f"_s{k}" if k else ""))
            for r, k in zip(resumen.itertuples(), semilla)]
con_nodos = [c / "nodos.csv" for c in carpetas if (c / "nodos.csv").exists()]  # las primeras del Exp. 3 no lo tienen
nodos = pd.concat([pd.read_csv(f) for f in con_nodos], ignore_index=True) if con_nodos else pd.DataFrame()
nodos.to_csv(d / "model_verification_full.csv")

print(f"{len(resumen)} corridas. Topología igual a la de los autores en todas: {resumen.MISMA_TOPOLOGIA.all()}")
print(f"Máx. diferencia con los autores: {resumen.filter(like='MAXDIF').to_numpy().max():.1e}")
print("\nTiempo medio de FLoRa [s] (con corridas en paralelo):")
print(resumen.pivot_table(index="NUM_END_DEVICES", columns="NUM_GATEWAYS", values="T_FLORA_S").round(1))

if len(resumen) < 80:
    sys.exit(f"\nFaltan {80 - len(resumen)} corridas para las Tablas 6 y 7.")

eds = nodos[nodos.END_DEVICE.notna()].copy()
eds["err_pdr"] = eds.flora_PDR - eds.model_PDR
eds["err_ee"] = eds.flora_EE - eds.model_EE
por_config = eds.groupby(["NUM_END_DEVICES", "NUM_GATEWAYS"]).agg(
    mae_pdr=("err_pdr", lambda e: e.abs().mean()), sde_pdr=("err_pdr", "std"),
    mae_ee=("err_ee", lambda e: e.abs().mean()), sde_ee=("err_ee", "std"))

print("\nTabla 6: MAE PDR ×10⁻² (SDE)")
t6 = por_config.apply(lambda r: f"{r.mae_pdr * 100:.3f} ({r.sde_pdr * 100:.3f})", axis=1)
print(t6.unstack("NUM_GATEWAYS"))
print("\nTabla 7: MAE EE bits/mJ (SDE)")
t7 = por_config.apply(lambda r: f"{r.mae_ee:.3f} ({r.sde_ee:.3f})", axis=1)
print(t7.unstack("NUM_GATEWAYS"))

# H2: el paper mezcla el promedio por nodo (resumen) con el promedio de la tabla (texto)
mae_pdr, mae_ee = eds.err_pdr.abs().mean(), eds.err_ee.abs().mean()
print(f"\nMAE por nodo:   PDR {mae_pdr * 100:.3f}×10⁻²   EE {mae_ee:.4f} bits/mJ   (paper: 0,940×10⁻² y 0,040)")
print(f"MAE por tabla:  PDR {por_config.mae_pdr.mean() * 100:.3f}×10⁻²   EE {por_config.mae_ee.mean():.4f} bits/mJ")
ok = mae_pdr <= MAE_PDR_MAX and mae_ee <= MAE_EE_MAX
print(f"Criterio D12 (MAE PDR ≤ 2×10⁻², MAE EE ≤ 0,08): {'cumple' if ok else 'NO cumple'}")
