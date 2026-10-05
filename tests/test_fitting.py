import json

import numpy as np
import pytest

from biofit import MODELS, __version__, fit_family, fit_model, load_data, save_results, validate_data
from biofit.cli import main
from biofit.estimation import initial_guess

T = np.linspace(0.5, 50, 25)

# Parâmetros "verdadeiros" usados para gerar dados sintéticos de cada modelo
TRUE_PARAMS = {
    "gompertz": [100, 5, 10],
    "logistic": [100, 0.2, 25],
    "hill": [100, 20, 3],
    "boltzmann": [5, 95, 25, 4],
    "first_order": [80, 0.08],
    "exponential_growth": [2, 0.07],
    "double_exponential": [60, 0.3, 40, 0.03],
    "gaussian": [50, 25, 6],
    "lognormal": [500, 3, 0.4],
    "lorentzian": [50, 25, 5, 2],
    "linear": [1.5, 3],
    "quadratic": [0.02, 0.5, 1],
}


def noisy(name, rel=0.01, seed=0):
    y = MODELS[name].func(T, *TRUE_PARAMS[name])
    return y + np.random.default_rng(seed).normal(0, rel * np.ptp(y), len(T))


def test_every_model_has_true_params():
    assert set(TRUE_PARAMS) == set(MODELS)


@pytest.mark.parametrize("name", sorted(MODELS))
def test_initial_guess_has_right_length(name):
    assert len(initial_guess(name, T, noisy(name))) == len(MODELS[name].params)


@pytest.mark.parametrize("name", sorted(MODELS))
def test_fit_recovers_synthetic_data(name):
    result = fit_model(name, T, noisy(name))
    assert result is not None
    assert result.r2 > 0.99


def test_family_ranks_by_aic():
    results = fit_family("sigmoidal", T, noisy("logistic"))
    assert results
    assert [r.aic for r in results] == sorted(r.aic for r in results)


def test_validate_rejects_too_few_points():
    with pytest.raises(ValueError):
        validate_data([1, 2, 3], [1, 2, 3])


def test_validate_rejects_nan():
    with pytest.raises(ValueError):
        validate_data(T, np.full_like(T, np.nan))


def test_lognormal_skipped_for_nonpositive_time():
    t = np.linspace(0, 10, 10)
    assert fit_model("lognormal", t, np.ones_like(t) + t) is None


def test_load_csv_and_txt_agree(tmp_path):
    t, y = np.arange(6.0), np.arange(6.0) ** 2
    csv, txt = tmp_path / "d.csv", tmp_path / "d.txt"
    np.savetxt(csv, np.column_stack([t, y]), delimiter=",", header="time,response", comments="")
    np.savetxt(txt, np.column_stack([t, y]))
    for path in (csv, txt):
        lt, ly = load_data(path)
        np.testing.assert_allclose(lt, t)
        np.testing.assert_allclose(ly, y)


def test_cli_writes_outputs(tmp_path):
    data = tmp_path / "d.csv"
    np.savetxt(data, np.column_stack([T, noisy("gompertz")]), delimiter=",",
               header="time,response", comments="")
    out = tmp_path / "out"

    assert main([str(data), "--family", "sigmoidal", "-o", str(out)]) == 0
    summary = json.loads((out / "fit_results.json").read_text())
    assert summary["best_model"] in MODELS
    assert summary["format_version"] == 1
    assert summary["biofit_version"] == __version__
    assert summary["source_file"] == "d.csv"
    assert summary["variable"] is None
    assert summary["units"] == {"time": None, "response": None}
    assert (out / "fitted_curve.csv").exists()
    assert (out / "fit_plot.png").exists()


def test_cli_records_variable_and_units(tmp_path):
    data = tmp_path / "d.csv"
    np.savetxt(data, np.column_stack([T, noisy("logistic")]), delimiter=",",
               header="time,response", comments="")
    out = tmp_path / "out"

    assert main([str(data), "-m", "logistic", "-o", str(out), "--no-plot",
                 "--variable", "biomass", "--time-unit", "h", "--response-unit", "g/L"]) == 0
    summary = json.loads((out / "fit_results.json").read_text())
    assert summary["variable"] == "biomass"
    assert summary["units"] == {"time": "h", "response": "g/L"}


def test_save_results_writes_strict_json(tmp_path):
    result = fit_model("logistic", T, noisy("logistic"))
    result.covariance = np.full_like(result.covariance, np.nan)
    save_results([result], T, noisy("logistic"), tmp_path)

    text = (tmp_path / "fit_results.json").read_text()
    assert "NaN" not in text
    summary = json.loads(text)
    assert all(v is None for v in summary["results"][0]["std_errors"].values())


def test_save_results_rejects_unknown_variable(tmp_path):
    result = fit_model("linear", T, noisy("linear"))
    with pytest.raises(ValueError):
        save_results([result], T, noisy("linear"), tmp_path, variable="enzyme")
