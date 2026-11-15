"""Variantes de FAST-LoRa, una por cabo suelto, contra FLoRa en las topologías del Exp. 1 y del Exp. 2.

Uso (desde Proyecto/):  scripts/sim.sh python scripts/variantes.py
Referencia: PDR y EE de FLoRa de los CSV de los autores (third_party/resultados_autores), que nuestra réplica reproduce.
La variante "base" debe dar exactamente el model_PDR/model_EE de esos CSV; si no, el script se detiene.
Escribe results/variantes/{exp1,exp2}_resumen.csv, exp2_por_config.csv y exp2_nodos.csv.
"""
import os
import sys
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import erf

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "third_party/MultiAgent-MARLTC/src"))
os.chdir(RAIZ)

from lora_model import LoraModel  # noqa: E402

# Corriente de TX [mA] por potencia [dBm] en energyConsumptionParameters.xml de los autores (H11)
CORRIENTE_TX_FLORA = {2: 26.34, 4: 29.65, 6: 34.03, 8: 37.28, 10: 44.53, 12: 52.33, 14: 62.46, 16: 74.80}
TENSION_FLORA = 3.3
PAYLOAD_FLORA_B = 20  # LoRaTransmitter.cc, nodos (H10)


class Variante(LoraModel):
    """LoraModel con los cabos sueltos como parámetros. Los valores por defecto son los del código original."""

    def __init__(self, *args, div_erf=2 * np.sqrt(2), omega_fila_victima=False, umbral_mismo_sf=6,
                 simb_libres=5, toa="modelo", potencia="modelo", **kwargs):
        self.div_erf = div_erf                        # ec. (11): divisor de la erf en unidades de σ (H4)
        self.omega_fila_victima = omega_fila_victima  # C4
        self.omega = self.INTER_SF_INTERFERENCE.copy()
        np.fill_diagonal(self.omega, umbral_mismo_sf)  # C2
        self.simb_libres = simb_libres                # C3: últimos símbolos del preámbulo que deben quedar limpios
        self.toa = toa                                # "modelo" | "implicita" (−20H, H5) | "flora" (H10)
        self.potencia = potencia                      # "modelo" (Liando) | "flora" (H11)
        super().__init__(*args, **kwargs)

    @cached_property
    def transmission_and_symbol_time(self):
        if self.toa == "modelo":
            return LoraModel.transmission_and_symbol_time.func(self)
        sf = self._sf
        ts = np.power(2, sf) / (self.BANDWIDTH * 1000)
        if self.toa == "implicita":
            de = ((sf >= 11) & (sf <= 12)).astype(int)
            bloques = np.ceil((self.PAYLOAD_SIZE - 4 * sf + 28 + 16 - 20) / (4 * (sf - 2 * de)))
            simb = 8 + np.maximum(bloques * (self.CODING_RATE + 4), 0)
        else:  # flora: 20 B fijos, DE = 0, división entera y 8 símbolos de más
            n = 8 + ((8 * PAYLOAD_FLORA_B - 4 * sf + 28 + 16) // (4 * sf)) * (self.CODING_RATE + 4)
            simb = 8 + n
        return (self.PREAMBLE_LEN + 4.25) * ts + simb * ts, ts

    @cached_property
    def p_not_corrupted(self):
        # Misma estructura que LoraModel.p_not_corrupted (tráfico Poisson)
        t, ts = self.transmission_and_symbol_time
        intervalo = (t - (self.PREAMBLE_LEN - self.simb_libres) * ts).reshape(-1, 1) + t
        np.fill_diagonal(intervalo, 0)
        lambda_rate = 1 / self._packet_interval
        p_tx = 1 - np.exp(-lambda_rate * intervalo)
        i = self._sf - 7
        w = self.omega[i.reshape(-1, 1), i] if self.omega_fila_victima else self.omega[i, i.reshape(-1, 1)]
        dif = self.rss_no_flat_fading[:, np.newaxis, :] - self.rss_no_flat_fading[np.newaxis, :, :]
        p_rss = 0.5 + 0.5 * erf((w[:, :, np.newaxis] - dif) / (self.div_erf * self.FLAT_FADING))
        return np.prod(1 - p_tx[:, :, np.newaxis] * p_rss, axis=1)

    @cached_property
    def ee(self):
        if self.potencia == "modelo":
            return LoraModel.ee.func(self)
        t, _ = self.transmission_and_symbol_time
        p_mw = TENSION_FLORA * np.vectorize(CORRIENTE_TX_FLORA.get)(self._tp)
        return self.PAYLOAD_SIZE / (p_mw * t / np.maximum(self.pdr, self._ALMOST_ZERO))


COMO_FLORA = dict(div_erf=2, omega_fila_victima=True, umbral_mismo_sf=1, simb_libres=6, toa="flora", potencia="flora")
VARIANTES = {
    "base": {},
    "ec11_raiz2": dict(div_erf=2),  # desviación √2·σ → erf(x / 2σ)
    "omega_fila_victima": dict(omega_fila_victima=True),
    "mismo_sf_1dB": dict(umbral_mismo_sf=1),
    "preambulo_6": dict(simb_libres=6),
    "cabecera_implicita": dict(toa="implicita"),
    "toa_potencia_flora": dict(toa="flora", potencia="flora"),
    "como_flora": COMO_FLORA,
    "como_flora_sin_toa_potencia": {k: v for k, v in COMO_FLORA.items() if k not in ("toa", "potencia")},
}


def errores(flora_pdr, flora_ee, pdr, ee) -> dict:
    e_pdr, e_ee = flora_pdr - pdr, flora_ee - ee
    return {"MAE_PDR": np.abs(e_pdr).mean(), "SDE_PDR": e_pdr.std(ddof=1),
            "MAE_EE": np.abs(e_ee).mean(), "SDE_EE": e_ee.std(ddof=1)}


def exp1(salida: Path):
    d = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_simple.csv", index_col=0)
    filas = []
    for nombre, kw in VARIANTES.items():
        pdr, ee = np.empty(len(d)), np.empty(len(d))
        for k, r in enumerate(d.itertuples()):
            m = Variante(1, 1, np.array([[0, r.DIST]]), np.array([[0, 0]]),
                         np.array([r.TP], dtype=np.int32), np.array([r.SF], dtype=np.int32), **kw)
            pdr[k], ee[k] = m.pdr[0], m.ee[0]
        if nombre == "base":
            dif = max(np.abs(pdr - d.model_pdr).max(), np.abs(ee - d.model_ee).max())
            assert dif < 1e-12, f"Exp. 1: la variante base no reproduce el modelo de los autores ({dif:.1e})"
        filas.append({"VARIANTE": nombre, **errores(d.flora_pdr, d.flora_ee, pdr, ee)})
    res = pd.DataFrame(filas)
    res.to_csv(salida / "exp1_resumen.csv", index=False)
    return res


def exp2(salida: Path):
    d = pd.read_csv(RAIZ / "third_party/resultados_autores/model_verification_full.csv", index_col=0)
    eds = d[d.END_DEVICE.notna()].copy()
    claves = ["NUM_END_DEVICES", "NUM_GATEWAYS", "RUN_NO"]
    for nombre, kw in VARIANTES.items():
        pdr, ee = pd.Series(np.nan, index=eds.index), pd.Series(np.nan, index=eds.index)
        for (n, g, rep), grupo in d.groupby(claves):
            gw = grupo[grupo.GATEWAY.notna()].sort_values("GATEWAY")
            ed = grupo[grupo.END_DEVICE.notna()].sort_values("END_DEVICE")
            m = Variante(int(n), int(g), ed[["POS_X", "POS_Y"]].to_numpy(), gw[["POS_X", "POS_Y"]].to_numpy(),
                         ed.TP.to_numpy(np.int32), ed.SF.to_numpy(np.int32), **kw)
            pdr[ed.index], ee[ed.index] = m.pdr, m.ee
        eds[f"{nombre}_PDR"], eds[f"{nombre}_EE"] = pdr, ee
        if nombre == "base":
            dif = max((pdr - eds.model_PDR).abs().max(), (ee - eds.model_EE).abs().max())
            assert dif < 1e-12, f"Exp. 2: la variante base no reproduce el modelo de los autores ({dif:.1e})"

    eds.to_csv(salida / "exp2_nodos.csv", index=False)
    resumen = pd.DataFrame([{"VARIANTE": v, **errores(eds.flora_PDR, eds.flora_EE, eds[f"{v}_PDR"], eds[f"{v}_EE"])}
                            for v in VARIANTES])
    resumen.to_csv(salida / "exp2_resumen.csv", index=False)
    por_config = pd.concat(
        [pd.DataFrame({"VARIANTE": v, **errores(g.flora_PDR, g.flora_EE, g[f"{v}_PDR"], g[f"{v}_EE"])}, index=[0])
         .assign(NUM_END_DEVICES=n, NUM_GATEWAYS=gw)
         for v in VARIANTES for (n, gw), g in eds.groupby(["NUM_END_DEVICES", "NUM_GATEWAYS"])],
        ignore_index=True)
    por_config.to_csv(salida / "exp2_por_config.csv", index=False)
    return resumen


if __name__ == "__main__":
    salida = RAIZ / "results/variantes"
    salida.mkdir(parents=True, exist_ok=True)
    fmt = {"MAE_PDR": lambda x: f"{x * 100:.3f}", "SDE_PDR": lambda x: f"{x * 100:.3f}",
           "MAE_EE": "{:.4f}".format, "SDE_EE": "{:.4f}".format}
    print("Exp. 1 (144 casos, 1 nodo) · PDR en ×10⁻², EE en bits/mJ")
    print(exp1(salida).to_string(index=False, formatters=fmt))
    print("\nExp. 2 (80 topologías, 13 200 nodos) · PDR en ×10⁻², EE en bits/mJ")
    print(exp2(salida).to_string(index=False, formatters=fmt))
