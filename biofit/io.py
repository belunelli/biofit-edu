"""Leitura de dados experimentais e exportação de resultados."""
import json
from pathlib import Path

import numpy as np

from . import __version__

# Versão do formato de fit_results.json; incremente ao mudar a estrutura
FORMAT_VERSION = 1

VARIABLES = ("biomass", "substrate", "product", "biogas", "other")


def load_data(path):
    """Lê um arquivo de duas colunas (tempo, resposta).

    `.csv` é lido com vírgula e uma linha de cabeçalho; `.txt`/`.ent`
    são lidos separados por espaços, sem cabeçalho.
    """
    path = Path(path)
    if path.suffix.lower() == ".csv":
        data = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    else:
        data = np.loadtxt(path, ndmin=2)
    if data.shape[1] != 2:
        raise ValueError(f"{path} deve ter exatamente 2 colunas (tempo, resposta).")
    return data[:, 0], data[:, 1]


def _finite_or_none(obj):
    """Troca NaN/inf por None, já que JSON válido não admite esses valores."""
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: _finite_or_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_finite_or_none(v) for v in obj]
    return obj


def save_results(results, t, y, out_dir, n_points=100, variable=None,
                 time_unit=None, response_unit=None, source=None):
    """Grava o resumo em JSON e a curva do melhor modelo em CSV.

    `variable` indica o que a resposta representa (um de `VARIABLES`);
    `time_unit` e `response_unit` são textos livres, como "h" e "g/L".
    São registrados para que outras ferramentas interpretem os parâmetros.
    """
    if variable is not None and variable not in VARIABLES:
        raise ValueError(f"Variável desconhecida: {variable!r}. Opções: {', '.join(VARIABLES)}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best = results[0]

    summary = {
        "format_version": FORMAT_VERSION,
        "biofit_version": __version__,
        "source_file": Path(source).name if source else None,
        "variable": variable,
        "units": {"time": time_unit, "response": response_unit},
        "best_model": best.name,
        "selection_criterion": "AIC",
        "results": [r.as_dict() for r in results],
        "data": {"t": np.asarray(t).tolist(), "y": np.asarray(y).tolist()},
    }
    text = json.dumps(_finite_or_none(summary), indent=2, ensure_ascii=False, allow_nan=False)
    (out_dir / "fit_results.json").write_text(text)

    t_fit = np.linspace(np.min(t), np.max(t), n_points)
    np.savetxt(out_dir / "fitted_curve.csv", np.column_stack([t_fit, best.predict(t_fit)]),
               delimiter=",", header="time,response", comments="", fmt="%.6g")
    return out_dir
