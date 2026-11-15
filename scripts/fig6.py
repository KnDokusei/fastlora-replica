"""Datos de la Fig. 6 (tiempo de ejecución de FLoRa y FAST-LoRa): artículo contra réplica (Exp. 3).

Uso (desde Proyecto/):  .venv/bin/python scripts/fig6.py
Lee results/exp3_fig6/tiempos.csv y escribe Figuras/datos/fig6.dat; la figura es Figuras/fig6.tex.
Los valores del artículo salen de los vectores de su Fig. 6 (pág. 13 del PDF, `mutool trace`):
alto de cada barra y de cada barra de error, con el eje calibrado en sus marcas de 10⁻³ a 10².
Las barras de error del artículo son simétricas en escala lineal, así que se leen como ±1 desviación estándar.
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "Figuras" / "datos"

# Artículo: media y desviación estándar sobre 1–5 GW; FLoRa en s, FAST-LoRa en ms
ARTICULO = pd.DataFrame({
    "N": [10, 20, 50, 100, 200],
    "flora_art": [15.17, 20.19, 49.21, 108.57, 316.35],
    "flora_art_std": [1.38, 4.30, 5.96, 8.71, 27.81],
    "fast_art_ms": [0.613, 0.641, 0.960, 2.570, 7.958],
    "fast_art_std_ms": [0.144, 0.118, 0.188, 1.831, 3.592],
}).set_index("N")


def main():
    t = pd.read_csv(RAIZ / "results/exp3_fig6/tiempos.csv")
    # Réplica: 15 corridas por tamaño (5 GW × 3 repeticiones); el modelo ya viene promediado en 20 ejecuciones
    rep = t.groupby("NUM_END_DEVICES").agg(
        flora_rep=("T_FLORA_S", "mean"), flora_rep_std=("T_FLORA_S", "std"),
        fast_rep_ms=("T_MODELO_MS", "mean"), fast_rep_std_ms=("T_MODELO_MS", "std"),
        corridas=("T_FLORA_S", "size"))
    rep.index.name = "N"
    d = ARTICULO.join(rep)
    assert (d.corridas == 15).all()

    # Todo en segundos para el eje logarítmico común
    for c in ["fast_art", "fast_art_std", "fast_rep", "fast_rep_std"]:
        d[c] = d[f"{c}_ms"] * 1e-3
    d["acel_art"] = d.flora_art / d.fast_art
    d["acel_rep"] = d.flora_rep / d.fast_rep

    SALIDA.mkdir(parents=True, exist_ok=True)
    cols = ["flora_art", "flora_art_std", "fast_art", "fast_art_std",
            "flora_rep", "flora_rep_std", "fast_rep", "fast_rep_std", "acel_art", "acel_rep"]
    d[cols].to_csv(SALIDA / "fig6.dat", sep=" ", float_format="%.6g")
    print(d[["flora_art", "flora_rep", "fast_art_ms", "fast_rep_ms", "acel_art", "acel_rep"]]
          .to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main()
