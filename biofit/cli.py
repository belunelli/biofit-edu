"""Interface de linha de comando do BioFIT."""
import argparse
import sys

from . import __version__
from .fitting import fit_family, fit_model, validate_data
from .io import VARIABLES, load_data, save_results
from .models import FAMILIES, MODELS


def build_parser():
    parser = argparse.ArgumentParser(
        prog="biofit",
        description="Ajuste de modelos cinéticos a dados de bioprocessos.",
    )
    parser.add_argument("data", help="arquivo com 2 colunas: tempo, resposta (.csv, .txt ou .ent)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--family", choices=FAMILIES,
                       help="ajusta todos os modelos da família e escolhe o melhor por AIC")
    group.add_argument("-m", "--model", choices=sorted(MODELS),
                       help="ajusta um único modelo")
    parser.add_argument("-o", "--output", default="results",
                        help="diretório de saída (padrão: results)")
    parser.add_argument("--variable", choices=VARIABLES,
                        help="o que a resposta representa (registrado em fit_results.json)")
    parser.add_argument("--time-unit", help='unidade do tempo, ex.: "h"')
    parser.add_argument("--response-unit", help='unidade da resposta, ex.: "g/L"')
    parser.add_argument("--xlabel", help="rótulo do eixo x (padrão: Tempo [unidade])")
    parser.add_argument("--ylabel", help="rótulo do eixo y (padrão: Resposta [unidade])")
    parser.add_argument("--no-plot", action="store_true", help="não gera o gráfico")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def axis_label(text, unit):
    return f"{text} [{unit}]" if unit else text


def print_table(results):
    print(f"\n{'Modelo':<20}{'R²':>10}{'AIC':>12}{'BIC':>12}")
    print("-" * 54)
    for r in results:
        print(f"{r.name:<20}{r.r2:>10.4f}{r.aic:>12.2f}{r.bic:>12.2f}")

    best = results[0]
    print(f"\nMelhor modelo: {best.name}")
    print(f"  {best.model.equation}")
    for name, value, se in zip(best.model.params, best.params, best.std_errors):
        print(f"  {name:<8} = {value:12.5g}  ± {se:.3g}")


def main(argv=None):
    args = build_parser().parse_args(argv)

    t, y = load_data(args.data)
    for warning in validate_data(t, y):
        print(f"Aviso: {warning}")

    if args.model:
        result = fit_model(args.model, t, y)
        results = [result] if result else []
    else:
        results = fit_family(args.family, t, y)

    if not results:
        print("Nenhum modelo convergiu.", file=sys.stderr)
        return 1

    print_table(results)
    out_dir = save_results(results, t, y, args.output, variable=args.variable,
                           time_unit=args.time_unit, response_unit=args.response_unit,
                           source=args.data)

    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from .plotting import plot_fits

        xlabel = args.xlabel or axis_label("Tempo", args.time_unit)
        ylabel = args.ylabel or axis_label("Resposta", args.response_unit)
        ax = plot_fits(t, y, results, xlabel, ylabel)
        ax.figure.savefig(out_dir / "fit_plot.png", dpi=150, bbox_inches="tight")
        plt.close(ax.figure)

    print(f"\nResultados gravados em {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
