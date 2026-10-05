import json

import numpy as np
import pytest

from biofit import load_data
from biofit.digitize import calibrate, data_to_pixels, pixels_to_data, save

# Eixo X: pixel 100 → 0 h, pixel 500 → 40 h
# Eixo Y (pixels crescem para baixo): pixel 400 → 0 g/L, pixel 50 → 350 g/L
X_CAL = calibrate([100, 500], [0, 40])
Y_CAL = calibrate([400, 50], [0, 350])


def test_calibrate_maps_reference_points():
    slope, intercept = X_CAL
    assert slope * 100 + intercept == pytest.approx(0)
    assert slope * 500 + intercept == pytest.approx(40)


def test_calibrate_handles_inverted_y_axis():
    assert Y_CAL[0] < 0


@pytest.mark.parametrize("pixels, values", [
    ([100, 100], [0, 10]),
    ([100, 200], [5, 5]),
    ([100], [0]),
])
def test_calibrate_rejects_degenerate_input(pixels, values):
    with pytest.raises(ValueError):
        calibrate(pixels, values)


def test_pixels_to_data_converts_and_sorts():
    clicks = [[300, 225], [100, 400], [500, 50]]
    data = pixels_to_data(clicks, X_CAL, Y_CAL)
    np.testing.assert_allclose(data, [[0, 0], [20, 175], [40, 350]])


def test_round_trip():
    clicks = np.array([[120.5, 380.0], [250.0, 210.3], [480.0, 60.0]])
    data = pixels_to_data(clicks, X_CAL, Y_CAL)
    np.testing.assert_allclose(data_to_pixels(data, X_CAL, Y_CAL), clicks)


def test_save_writes_csv_and_metadata(tmp_path):
    data = pixels_to_data([[100, 400], [300, 225], [500, 50]], X_CAL, Y_CAL)
    csv_path, meta_path = save(data, tmp_path / "sub" / "fig1.csv", {"source_image": "fig1.png"})

    t, y = load_data(csv_path)
    np.testing.assert_allclose(np.column_stack([t, y]), data)

    assert meta_path.name == "fig1_metadata.json"
    meta = json.loads(meta_path.read_text())
    assert meta["source_image"] == "fig1.png"
    assert meta["output_csv"] == "fig1.csv"


def test_interactive_flow_with_simulated_clicks(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from biofit import digitize as dz

    image = tmp_path / "fig.png"
    plt.imsave(image, np.ones((450, 600, 3)))

    # 1º eixo X com um clique só (deve repetir), depois X, Y, curva vazia (repete), curva
    clicks = iter([
        [(100, 420)],
        [(100, 420), (500, 420)],
        [(90, 400), (90, 50)],
        [],
        [(300, 225), (100, 400), (500, 50)],
    ])
    answers = iter(["0", "40", "0", "350,0", "s"])
    monkeypatch.setattr(plt, "ginput", lambda *a, **k: next(clicks))
    monkeypatch.setattr(plt, "show", lambda *a, **k: None)
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    monkeypatch.setattr(dz, "_has_gui", lambda: True)

    out = tmp_path / "fig.csv"
    assert dz.main([str(image), str(out)]) == 0

    t, y = load_data(out)
    np.testing.assert_allclose(np.column_stack([t, y]), [[0, 0], [20, 175], [40, 350]])
    meta = json.loads((tmp_path / "fig_metadata.json").read_text())
    assert meta["n_points"] == 3
    assert meta["calibration"]["y"]["values"] == [0.0, 350.0]


def test_main_without_gui_explains_how_to_fix(tmp_path, capsys):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from biofit import digitize as dz

    image = tmp_path / "fig.png"
    plt.imsave(image, np.ones((10, 10, 3)))

    assert dz.main([str(image), str(tmp_path / "fig.csv")]) == 1
    assert "python3-tk" in capsys.readouterr().err
    assert not (tmp_path / "fig.csv").exists()
