"""Ajuste por mínimos quadrados não lineares e seleção de modelos por AIC."""
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import curve_fit

from .estimation import initial_guess
from .models import MODELS, Model, models_in_family

MIN_POINTS = 5


@dataclass
class FitResult:
    model: Model
    params: np.ndarray
    covariance: np.ndarray
    r2: float
    aic: float
    bic: float
    n: int
    initial_params: list = field(default_factory=list)

    @property
    def name(self):
        return self.model.name

    @property
    def std_errors(self):
        return np.sqrt(np.diag(self.covariance))

    def predict(self, t):
        return self.model.func(np.asarray(t, float), *self.params)

    def as_dict(self):
        return {
            "model": self.name,
            "equation": self.model.equation,
            "parameters": dict(zip(self.model.params, self.params.tolist())),
            "std_errors": dict(zip(self.model.params, self.std_errors.tolist())),
            "r2": self.r2,
            "aic": self.aic,
            "bic": self.bic,
            "n_points": self.n,
        }


def validate_data(t, y):
    """Verifica problemas que impedem o ajuste; retorna lista de avisos."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    if not (np.all(np.isfinite(t)) and np.all(np.isfinite(y))):
        raise ValueError("Os dados contêm valores NaN ou infinitos.")
    if len(t) < MIN_POINTS:
        raise ValueError(f"São necessários pelo menos {MIN_POINTS} pontos (recebidos: {len(t)}).")
    if np.ptp(y) < 1e-10:
        raise ValueError("A resposta é praticamente constante.")

    warnings = []
    if not np.all(np.diff(t) > 0):
        warnings.append("O tempo não é estritamente crescente; considere ordenar os dados.")
    return warnings


def _domain_ok(name, t, y):
    if name == "lognormal":
        return np.all(t > 0)
    if name == "exponential_growth":
        return np.all(y > 0)
    return True


def information_criteria(n, rss, k):
    """AIC e BIC para erros gaussianos (forma baseada na RSS)."""
    if rss <= 0:
        return -np.inf, -np.inf
    base = n * np.log(rss / n)
    return base + 2 * k, base + k * np.log(n)


def fit_model(name, t, y, p0=None, maxfev=5000):
    """Ajusta um modelo pelo nome. Retorna FitResult ou None se não convergir."""
    model = MODELS[name]
    t, y = np.asarray(t, float), np.asarray(y, float)
    if not _domain_ok(name, t, y):
        return None
    p0 = list(p0) if p0 is not None else initial_guess(name, t, y)
    # Overflow/NaN em iterações intermediárias é normal e não indica falha
    with np.errstate(all="ignore"):
        try:
            params, cov = curve_fit(model.func, t, y, p0=p0, maxfev=maxfev)
        except (RuntimeError, ValueError):
            return None
    if not np.all(np.isfinite(cov)):
        cov = np.full((len(params), len(params)), np.nan)

    residuals = y - model.func(t, *params)
    rss = float(np.sum(residuals**2))
    r2 = 1 - rss / float(np.sum((y - y.mean()) ** 2))
    aic, bic = information_criteria(len(y), rss, len(params))
    return FitResult(model, params, cov, r2, aic, bic, len(y), p0)


def fit_family(family, t, y):
    """Ajusta todos os modelos de uma família, ordenados por AIC (melhor primeiro)."""
    results = [fit_model(m.name, t, y) for m in models_in_family(family)]
    return sorted((r for r in results if r is not None), key=lambda r: r.aic)
