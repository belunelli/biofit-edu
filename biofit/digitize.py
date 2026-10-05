"""Extração interativa de pontos a partir de figuras publicadas.

Uso: python -m biofit.digitize figura.png saida.csv

1. Clique em dois pontos do eixo X e informe seus valores reais.
2. Clique em dois pontos do eixo Y e informe seus valores reais.
3. Clique nos pontos da curva (botão direito desfaz o último) e pressione ENTER.
4. Confira a pré-visualização e confirme a gravação.

São gravados o CSV (time,response) e um JSON de metadados com a imagem de
origem e a calibração usada, para rastreabilidade dos dados extraídos.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from . import __version__


def calibrate(pixels, values):
    """Mapeamento linear pixel → valor a partir de dois pontos de referência.

    Retorna (inclinação, intercepto).
    """
    if len(pixels) != 2 or len(values) != 2:
        raise ValueError("A calibração exige exatamente 2 pontos de referência.")
    (p1, p2), (v1, v2) = pixels, values
    if p1 == p2:
        raise ValueError("Os pontos de calibração devem estar em posições diferentes.")
    if v1 == v2:
        raise ValueError("Os valores de calibração devem ser diferentes.")
    slope = (v2 - v1) / (p2 - p1)
    return slope, v1 - slope * p1


def pixels_to_data(points, x_cal, y_cal):
    """Converte cliques (N × 2, em pixels) em dados reais ordenados pelo tempo."""
    points = np.asarray(points, float).reshape(-1, 2)
    data = np.column_stack([
        x_cal[0] * points[:, 0] + x_cal[1],
        y_cal[0] * points[:, 1] + y_cal[1],
    ])
    return data[np.argsort(data[:, 0])]


def data_to_pixels(data, x_cal, y_cal):
    """Operação inversa de `pixels_to_data`, usada na pré-visualização."""
    data = np.asarray(data, float).reshape(-1, 2)
    return np.column_stack([
        (data[:, 0] - x_cal[1]) / x_cal[0],
        (data[:, 1] - y_cal[1]) / y_cal[0],
    ])


def save(data, csv_path, metadata):
    """Grava o CSV e o JSON de metadados (`<nome>_metadata.json`) ao lado dele."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(csv_path, data, delimiter=",", header="time,response", comments="", fmt="%.6g")

    meta_path = csv_path.with_name(f"{csv_path.stem}_metadata.json")
    metadata = {**metadata, "output_csv": csv_path.name}
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    return csv_path, meta_path


# --- Parte interativa -------------------------------------------------------

def _clicks(img, title, n, markers=()):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(img)
    for pts, style in markers:
        ax.plot(pts[:, 0], pts[:, 1], style, ms=9, alpha=0.6)
    ax.set_title(title)
    ax.axis("off")
    # botão esquerdo adiciona, direito remove o último, ENTER encerra
    points = np.array(plt.ginput(n, timeout=0, mouse_add=1, mouse_pop=3, mouse_stop=2))
    plt.close(fig)
    return points.reshape(-1, 2)


def _ask_float(prompt):
    while True:
        try:
            return float(input(prompt).replace(",", "."))
        except ValueError:
            print("  Valor inválido; use um número (ex.: 10.5).")


def _calibrate_axis(img, axis, coord, markers=()):
    hint = "esquerda → direita" if axis == "X" else "baixo → cima"
    while True:
        pts = _clicks(img, f"Clique em 2 pontos do eixo {axis} ({hint})", 2, markers)
        if len(pts) != 2:
            print(f"  São necessários 2 cliques no eixo {axis}; tente novamente.")
            continue
        values = [_ask_float(f"Valor real de {axis} no ponto {i + 1}: ") for i in range(2)]
        try:
            return pts, values, calibrate(pts[:, coord], values)
        except ValueError as err:
            print(f"  {err} Tente novamente.")


def _preview(img, data, x_cal, y_cal):
    import matplotlib.pyplot as plt

    px = data_to_pixels(data, x_cal, y_cal)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(img)
    ax.plot(px[:, 0], px[:, 1], "o-", color="#D55E00", ms=6, lw=1.5,
            label=f"{len(data)} pontos extraídos")
    ax.set_title("Pré-visualização: feche a janela para continuar")
    ax.axis("off")
    ax.legend()
    plt.show()


def digitize(image_path):
    """Conduz a extração interativa. Retorna (dados, metadados)."""
    import matplotlib.image as mpimg

    img = mpimg.imread(image_path)

    x_px, x_vals, x_cal = _calibrate_axis(img, "X", 0)
    y_px, y_vals, y_cal = _calibrate_axis(img, "Y", 1, markers=[(x_px, "rs")])

    while True:
        pts = _clicks(img, "Clique nos pontos da curva (direito desfaz); ENTER para terminar",
                      -1, markers=[(x_px, "rs"), (y_px, "r^")])
        if len(pts) > 0:
            break
        print("  Nenhum ponto foi clicado; tente novamente.")

    data = pixels_to_data(pts, x_cal, y_cal)
    metadata = {
        "source_image": Path(image_path).name,
        "extraction_method": "biofit.digitize (matplotlib ginput)",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "biofit_version": __version__,
        "calibration": {
            "x": {"pixels": x_px[:, 0].tolist(), "values": x_vals},
            "y": {"pixels": y_px[:, 1].tolist(), "values": y_vals},
        },
        "n_points": len(data),
        "data_range": {
            "x": [float(data[:, 0].min()), float(data[:, 0].max())],
            "y": [float(data[:, 1].min()), float(data[:, 1].max())],
        },
    }
    _preview(img, data, x_cal, y_cal)
    return data, metadata


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__)
        return 1

    image, output = argv
    if not Path(image).is_file():
        print(f"Imagem não encontrada: {image}", file=sys.stderr)
        return 1

    data, metadata = digitize(image)
    if input("Gravar os pontos extraídos? [S/n] ").strip().lower() in ("n", "nao", "não"):
        print("Extração descartada.")
        return 1

    csv_path, meta_path = save(data, output, metadata)
    print(f"{len(data)} pontos gravados em {csv_path}")
    print(f"Metadados gravados em {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
