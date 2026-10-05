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
pip install -e .
```

## Uso rápido

### Linha de comando

```bash
# Ajusta todos os modelos sigmoidais e escolhe o melhor
biofit examples/data/sigmoidal.csv --family sigmoidal

# Ajusta um único modelo
biofit examples/data/sigmoidal.csv --model gompertz -o resultados/
```

Famílias: `sigmoidal`, `exponential`, `peak`, `polynomial`.

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
> initial modeling of bioprocess data* (versão 0.1.0) [Software].

## Licença

Distribuído sob a licença MIT, para fins acadêmicos e de pesquisa. Consulte o
arquivo [LICENSE](LICENSE).

## Autora

**Betânia Hoss Lunelli**
