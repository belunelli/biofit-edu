"""Estimativas iniciais de parâmetros a partir do perfil dos dados.

Bons chutes iniciais são o que faz o ajuste não linear convergir; as
heurísticas abaixo extraem platô, fase lag, taxa máxima e posição de pico
diretamente dos pontos experimentais.
"""
import numpy as np

PLATEAU_FACTOR = 1.1  # platô estimado um pouco acima do máximo observado
LAG_THRESHOLD = 0.1   # fração da amplitude que marca o fim da fase lag


def _profile(t, y):
    slopes = np.diff(y) / np.diff(t)
    i = int(np.argmax(np.abs(slopes)))
    peak = int(np.argmax(y))
    return {
        "y_min": y.min(), "y_max": y.max(), "y_range": np.ptp(y),
        "t_range": np.ptp(t),
        "max_slope": slopes[i], "max_slope_t": (t[i] + t[i + 1]) / 2,
        "peak": peak,
    }


def _half_width(t, y, peak, baseline=0.0):
    """Largura total à meia altura (FWHM) em torno do pico."""
    half = baseline + (y[peak] - baseline) / 2
    left = next((i for i in range(peak) if y[i] >= half), 0)
    right = next((i for i in range(peak, len(y)) if y[i] <= half), len(y) - 1)
    return t[right] - t[left]


def initial_guess(name, t, y):
    """Retorna a lista de parâmetros iniciais para o modelo `name`."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    p = _profile(t, y)
    slope = abs(p["max_slope"])

    if name == "gompertz":
        A = p["y_max"] * PLATEAU_FACTOR
        lag_idx = int(np.argmax(y >= p["y_min"] + LAG_THRESHOLD * p["y_range"]))
        return [A, slope, t[lag_idx]]

    if name == "logistic":
        K = p["y_max"] * PLATEAU_FACTOR
        return [K, 4 * slope / K, p["max_slope_t"]]

    if name == "hill":
        K = t[np.argmin(np.abs(y - p["y_max"] / 2))]
        n = float(np.clip(10 * slope / p["y_max"], 1.0, 5.0))
        return [p["y_max"] * PLATEAU_FACTOR, max(K, 1e-6), n]

    if name == "boltzmann":
        dx = p["t_range"] * p["y_range"] / (10 * slope) if slope else p["t_range"] * 0.1
        dx = float(np.clip(dx, 0.1, 0.3 * p["t_range"]))
        return [y[0], y[-1], p["max_slope_t"], dx]

    if name == "first_order":
        A = p["y_max"] * PLATEAU_FACTOR
        frac = y / A
        mask = (frac > 0) & (frac < 0.99)
        k = -np.polyfit(t[mask], np.log(1 - frac[mask]), 1)[0] if mask.sum() > 1 else 0.01
        return [A, max(k, 1e-3)]

    if name == "exponential_growth":
        mask = y > 0
        k = np.polyfit(t[mask], np.log(y[mask]), 1)[0] if mask.sum() > 1 else 0.01
        return [y[0] if y[0] > 0 else 1.0, k]

    if name == "double_exponential":
        return [0.6 * p["y_range"], 0.1, 0.4 * p["y_range"], 0.01]

    if name == "gaussian":
        sigma = _half_width(t, y, p["peak"]) / 2.355  # FWHM = 2·√(2·ln2)·σ
        return [y[p["peak"]], t[p["peak"]], max(sigma, 0.1 * p["t_range"])]

    if name == "lognormal":
        t_peak = t[p["peak"]]
        return [y[p["peak"]], np.log(t_peak) if t_peak > 0 else 1.0, 0.5]

    if name == "lorentzian":
        w = _half_width(t, y, p["peak"], baseline=p["y_min"]) / 2
        return [y[p["peak"]] - p["y_min"], t[p["peak"]], max(w, 0.1 * p["t_range"]), p["y_min"]]

    if name == "linear":
        return list(np.polyfit(t, y, 1))

    if name == "quadratic":
        return list(np.polyfit(t, y, 2))

    raise ValueError(f"Modelo desconhecido: {name!r}")
