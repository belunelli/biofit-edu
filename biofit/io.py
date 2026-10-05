"""Leitura de dados experimentais e exportação de resultados."""
import json
from pathlib import Path

import numpy as np


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


def save_results(results, t, y, out_dir, n_points=100):
    """Grava o resumo em JSON e a curva do melhor modelo em CSV."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best = results[0]

    summary = {
        "best_model": best.name,
        "selection_criterion": "AIC",
        "results": [r.as_dict() for r in results],
        "data": {"t": np.asarray(t).tolist(), "y": np.asarray(y).tolist()},
    }
    (out_dir / "fit_results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    t_fit = np.linspace(np.min(t), np.max(t), n_points)
    np.savetxt(out_dir / "fitted_curve.csv", np.column_stack([t_fit, best.predict(t_fit)]),
               delimiter=",", header="time,response", comments="", fmt="%.6g")
    return out_dir
