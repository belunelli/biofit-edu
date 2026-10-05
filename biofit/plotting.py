"""Gráficos de comparação entre modelos ajustados."""
import numpy as np
import matplotlib.pyplot as plt

# Paleta Okabe-Ito (segura para daltonismo)
DATA_COLOR = "#E69F00"
BEST_COLOR = "#0072B2"
OTHER_COLOR = "#999999"


def plot_fits(t, y, results, xlabel="Tempo", ylabel="Resposta", ax=None):
    """Plota os dados experimentais e as curvas ajustadas (melhor em destaque)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))

    t_curve = np.linspace(np.min(t), np.max(t), 300)
    for i, r in enumerate(results):
        best = i == 0
        ax.plot(t_curve, r.predict(t_curve),
                color=BEST_COLOR if best else OTHER_COLOR,
                lw=2.5 if best else 1.0, ls="-" if best else "--",
                label=f"{r.name} (R² = {r.r2:.3f})", zorder=3 if best else 2)

    ax.scatter(t, y, s=50, color=DATA_COLOR, edgecolor="white", zorder=4, label="Experimental")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if results:
        ax.set_title(f"Melhor ajuste: {results[0].name}")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    return ax
