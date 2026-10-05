# BioFIT

**BioFIT: a framework for generalized fitting and initial modeling of bioprocess data**

O BioFIT ajusta modelos cinéticos clássicos a dados experimentais de
bioprocessos (crescimento microbiano, consumo de substrato, formação de
produto, produção de biogás etc.), estima automaticamente os valores iniciais
dos parâmetros e seleciona o melhor modelo pelo critério de Akaike (AIC).

## Funcionalidades

- 12 modelos em 4 famílias: sigmoidal, exponencial, pico e polinomial
  ([lista completa](docs/modelos.md))
- Estimativa automática de parâmetros iniciais a partir do perfil dos dados
- Comparação de modelos por R², AIC e BIC, com erros-padrão dos parâmetros
- Exportação de resultados em JSON, da curva ajustada em CSV e do gráfico em PNG
- Ferramenta interativa para extrair pontos de figuras publicadas

## Instalação

Requer Python 3.9 ou superior.

```bash
git clone https://github.com/belunelli/biofit-edu.git
cd biofit-edu
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

O ambiente virtual (`.venv`) é necessário em distribuições Linux recentes
(Debian 12+, Ubuntu 23.04+), que bloqueiam `pip install` no Python do sistema
com o erro `externally-managed-environment`. Se o comando `python3 -m venv`
falhar, instale o módulo com `sudo apt install python3-venv`.

Ative o ambiente (`source .venv/bin/activate`) sempre que abrir um novo
terminal; sem isso, o comando `biofit` não é encontrado.

## Uso rápido

### Linha de comando

```bash
# Ajusta todos os modelos sigmoidais e escolhe o melhor
biofit examples/data/sigmoidal.csv --family sigmoidal

# Ajusta um único modelo
biofit examples/data/sigmoidal.csv --model gompertz -o resultados/

# Registra o que a resposta representa e as unidades
biofit examples/data/sigmoidal.csv --family sigmoidal \
    --variable biomass --time-unit h --response-unit g/L
```

Famílias: `sigmoidal`, `exponential`, `peak`, `polynomial`.

As opções `--variable` (`biomass`, `substrate`, `product`, `biogas` ou `other`),
`--time-unit` e `--response-unit` são opcionais. Quando informadas, ficam
registradas em `fit_results.json` e aparecem nos rótulos do gráfico, o que permite
que outras ferramentas interpretem os parâmetros ajustados sem ambiguidade.

Saída típica:

```
Modelo                      R²         AIC         BIC
------------------------------------------------------
gompertz                1.0000     -125.47     -124.27
boltzmann               0.9998      -12.96      -11.37
logistic                0.9971       17.10       18.30
hill                    0.9954       22.19       23.39

Melhor modelo: gompertz
  y = A·exp(-exp(mu·e/A·(lambda - t) + 1))
  A        =       101.45  ± 0.00375
  mu       =      0.70831  ± 4.63e-05
  lambda   =       3.8352  ± 0.00417
```

Arquivos gerados no diretório de saída (padrão `results/`):

| Arquivo | Conteúdo |
|---|---|
| `fit_results.json` | parâmetros, erros-padrão, R², AIC e BIC de todos os modelos |
| `fitted_curve.csv` | curva do melhor modelo (100 pontos) |
| `fit_plot.png` | dados experimentais e curvas ajustadas |

Estrutura de `fit_results.json`:

```json
{
  "format_version": 1,
  "biofit_version": "0.2.0",
  "source_file": "sigmoidal.csv",
  "variable": "biomass",
  "units": {"time": "h", "response": "g/L"},
  "best_model": "gompertz",
  "selection_criterion": "AIC",
  "results": [
    {
      "model": "gompertz",
      "equation": "y = A·exp(-exp(mu·e/A·(lambda - t) + 1))",
      "parameters": {"A": 101.45, "mu": 0.70831, "lambda": 3.8352},
      "std_errors": {"A": 0.00375, "mu": 4.63e-05, "lambda": 0.00417},
      "r2": 1.0, "aic": -125.47, "bic": -124.27, "n_points": 11
    }
  ],
  "data": {"t": [0.0, 20.0, 40.0], "y": [5.45, 13.73, 25.82]}
}
```

- `results` vem ordenado por AIC; o primeiro é o melhor modelo.
- `variable` e as unidades ficam `null` quando não informadas.
- Erros-padrão que não puderem ser estimados são gravados como `null`.
- `format_version` muda sempre que a estrutura do arquivo mudar.

### Em Python

```python
from biofit import load_data, fit_family, fit_model

t, y = load_data("examples/data/sigmoidal.csv")

results = fit_family("sigmoidal", t, y)   # ordenados por AIC
best = results[0]
print(best.name, best.params, best.r2)

gompertz = fit_model("gompertz", t, y)
y_pred = gompertz.predict([0, 50, 100])
```

## Formato dos dados

Arquivos com **duas colunas**: tempo e resposta, usando ponto como separador decimal.

- `.csv`: separado por vírgulas, com uma linha de cabeçalho
- `.txt` / `.ent`: separado por espaços, sem cabeçalho

```csv
time,response
0.0,5.45
20.0,13.73
40.0,25.82
```

São necessários pelo menos 5 pontos; recomenda-se ao menos 5 pontos por
parâmetro do modelo.

## Extração de dados de figuras

Para reutilizar dados publicados apenas em gráficos:

```bash
python -m biofit.digitize figura.png dados.csv
```

A extração abre uma janela do matplotlib, o que exige uma interface gráfica.
Em Linux/WSL, instale o Tk antes do primeiro uso (no WSL, é preciso também o
WSLg, do Windows 11, ou um servidor X):

```bash
sudo apt install python3-tk
```

1. Clique em dois pontos do eixo X e informe seus valores reais; repita para o eixo Y.
2. Clique sobre os pontos da curva (botão direito desfaz o último) e pressione ENTER.
3. Confira a pré-visualização dos pontos sobre a figura e confirme a gravação.

São gerados dois arquivos:

| Arquivo | Conteúdo |
|---|---|
| `dados.csv` | pontos extraídos (`time,response`), prontos para o `biofit` |
| `dados_metadata.json` | imagem de origem, calibração dos eixos, data e número de pontos |

Os metadados garantem a rastreabilidade dos dados extraídos. Ao publicar
resultados obtidos dessa forma, cite a fonte original da figura.

A conversão de pixels em valores também pode ser usada diretamente em Python:

```python
from biofit.digitize import calibrate, pixels_to_data

x_cal = calibrate([100, 500], [0, 40])    # pixels → valores do eixo X
y_cal = calibrate([400, 50], [0, 350])    # pixels → valores do eixo Y
dados = pixels_to_data([[300, 225], [500, 50]], x_cal, y_cal)
```

## Estrutura do repositório

```
biofit-edu/
├── biofit/
│   ├── models.py       # equações dos modelos
│   ├── estimation.py   # estimativas iniciais de parâmetros
│   ├── fitting.py      # ajuste, métricas e seleção por AIC
│   ├── io.py           # leitura de dados e exportação
│   ├── plotting.py     # gráficos
│   ├── digitize.py     # extração de pontos de figuras
│   └── cli.py          # interface de linha de comando
├── docs/modelos.md     # descrição dos modelos e critérios
├── examples/data/      # dados de exemplo
└── tests/              # testes automatizados
```

## Testes

```bash
pip install -e ".[dev]"
pytest
```

## Como citar

Se o BioFIT for útil em seu trabalho, cite-o conforme o arquivo
[`CITATION.cff`](CITATION.cff):

> Lunelli, B.H. (2026). *BioFIT: a framework for generalized fitting and
> initial modeling of bioprocess data* (versão 0.2.0) [Software].

## Licença

Distribuído sob a licença MIT, para fins acadêmicos e de pesquisa. Consulte o
arquivo [LICENSE](LICENSE).

## Autora

**Betânia Hoss Lunelli**
