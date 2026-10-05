"""BioFIT: ajuste generalizado e modelagem inicial de dados de bioprocessos."""
__version__ = "0.2.0"

from .fitting import FitResult, fit_family, fit_model, validate_data
from .io import load_data, save_results
from .models import FAMILIES, MODELS

__all__ = [
    "FAMILIES", "MODELS", "FitResult",
    "fit_family", "fit_model", "validate_data",
    "load_data", "save_results",
]
