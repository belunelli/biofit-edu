"""Catálogo de modelos cinéticos usados no ajuste de curvas.

Cada modelo é registrado com sua função, nomes de parâmetros, equação e
classe de perfil (sigmoidal, exponencial, pico ou polinomial).
"""
from dataclasses import dataclass
from typing import Callable

import numpy as np


# --- Sigmoidais -------------------------------------------------------------

def gompertz(t, A, mu, lam):
    """Gompertz modificado (Zwietering et al., 1990)."""
    return A * np.exp(-np.exp(mu * np.e / A * (lam - t) + 1))


def logistic(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))


def hill(t, Vmax, K, n):
    return Vmax * t**n / (K**n + t**n)


def boltzmann(t, A1, A2, x0, dx):
    return (A1 - A2) / (1 + np.exp((t - x0) / dx)) + A2


# --- Exponenciais -----------------------------------------------------------

def first_order(t, A, k):
    return A * (1 - np.exp(-k * t))


def exponential_growth(t, A, k):
    return A * np.exp(k * t)


def double_exponential(t, A1, k1, A2, k2):
    return A1 * np.exp(-k1 * t) + A2 * np.exp(-k2 * t)


# --- Pico -------------------------------------------------------------------

def gaussian(t, A, mu, sigma):
    return A * np.exp(-(t - mu) ** 2 / (2 * sigma**2))


def lognormal(t, A, mu, sigma):
    return A / (t * sigma * np.sqrt(2 * np.pi)) * np.exp(-(np.log(t) - mu) ** 2 / (2 * sigma**2))


def lorentzian(t, A, x0, w, y0):
    return A / (1 + ((t - x0) / w) ** 2) + y0


# --- Polinomiais ------------------------------------------------------------

def linear(t, a, b):
    return a * t + b


def quadratic(t, a, b, c):
    return a * t**2 + b * t + c


@dataclass(frozen=True)
class Model:
    name: str
    func: Callable
    params: tuple
    equation: str
    family: str


MODELS = {m.name: m for m in [
    Model("gompertz", gompertz, ("A", "mu", "lambda"),
          "y = A·exp(-exp(mu·e/A·(lambda - t) + 1))", "sigmoidal"),
    Model("logistic", logistic, ("K", "r", "t0"),
          "y = K / (1 + exp(-r·(t - t0)))", "sigmoidal"),
    Model("hill", hill, ("Vmax", "K", "n"),
          "y = Vmax·t^n / (K^n + t^n)", "sigmoidal"),
    Model("boltzmann", boltzmann, ("A1", "A2", "x0", "dx"),
          "y = (A1 - A2) / (1 + exp((t - x0)/dx)) + A2", "sigmoidal"),
    Model("first_order", first_order, ("A", "k"),
          "y = A·(1 - exp(-k·t))", "exponential"),
    Model("exponential_growth", exponential_growth, ("A", "k"),
          "y = A·exp(k·t)", "exponential"),
    Model("double_exponential", double_exponential, ("A1", "k1", "A2", "k2"),
          "y = A1·exp(-k1·t) + A2·exp(-k2·t)", "exponential"),
    Model("gaussian", gaussian, ("A", "mu", "sigma"),
          "y = A·exp(-(t - mu)² / (2·sigma²))", "peak"),
    Model("lognormal", lognormal, ("A", "mu", "sigma"),
          "y = A / (t·sigma·√(2π)) · exp(-(ln t - mu)² / (2·sigma²))", "peak"),
    Model("lorentzian", lorentzian, ("A", "x0", "w", "y0"),
          "y = A / (1 + ((t - x0)/w)²) + y0", "peak"),
    Model("linear", linear, ("a", "b"),
          "y = a·t + b", "polynomial"),
    Model("quadratic", quadratic, ("a", "b", "c"),
          "y = a·t² + b·t + c", "polynomial"),
]}

FAMILIES = ("sigmoidal", "exponential", "peak", "polynomial")


def models_in_family(family):
    """Retorna os modelos de uma família de perfil."""
    if family not in FAMILIES:
        raise ValueError(f"Família desconhecida: {family!r}. Opções: {', '.join(FAMILIES)}")
    return [m for m in MODELS.values() if m.family == family]
