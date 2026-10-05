# Modelos disponíveis

Os modelos estão agrupados por **família**, de acordo com o perfil da curva
experimental. Ao usar `--family`, todos os modelos da família são ajustados e
ordenados pelo Critério de Informação de Akaike (AIC).

## Sigmoidal (`sigmoidal`)

Curvas de crescimento com fase lag e platô (biomassa, produto acumulado, biogás).

| Modelo | Equação | Parâmetros |
|---|---|---|
| `gompertz` | y = A·exp(−exp(μ·e/A·(λ − t) + 1)) | A: assíntota; μ: taxa máxima; λ: fase lag |
| `logistic` | y = K / (1 + exp(−r·(t − t₀))) | K: capacidade; r: taxa; t₀: ponto de inflexão |
| `hill` | y = Vmax·tⁿ / (Kⁿ + tⁿ) | Vmax: máximo; K: meia saturação; n: cooperatividade |
| `boltzmann` | y = (A₁ − A₂) / (1 + exp((t − x₀)/dx)) + A₂ | A₁, A₂: platôs inicial e final; x₀: centro; dx: largura |

O modelo `gompertz` segue a forma reparametrizada de Zwietering et al. (1990),
em que os parâmetros têm interpretação biológica direta.

## Exponencial (`exponential`)

Crescimento ou decaimento exponencial (consumo de substrato, cinética de 1ª ordem).

| Modelo | Equação | Parâmetros |
|---|---|---|
| `first_order` | y = A·(1 − exp(−k·t)) | A: assíntota; k: constante de velocidade |
| `exponential_growth` | y = A·exp(k·t) | A: valor inicial; k: taxa específica (requer y > 0) |
| `double_exponential` | y = A₁·exp(−k₁·t) + A₂·exp(−k₂·t) | componentes rápida e lenta |

## Pico (`peak`)

Perfis com máximo intermediário (intermediários metabólicos, produção transiente).

| Modelo | Equação | Parâmetros |
|---|---|---|
| `gaussian` | y = A·exp(−(t − μ)² / (2σ²)) | A: altura; μ: posição; σ: largura |
| `lognormal` | y = A / (t·σ·√(2π))·exp(−(ln t − μ)² / (2σ²)) | pico assimétrico (requer t > 0) |
| `lorentzian` | y = A / (1 + ((t − x₀)/w)²) + y₀ | A: altura; x₀: centro; w: meia largura; y₀: linha de base |

## Polinomial (`polynomial`)

| Modelo | Equação |
|---|---|
| `linear` | y = a·t + b |
| `quadratic` | y = a·t² + b·t + c |

## Critérios de qualidade

Com *n* pontos, *k* parâmetros e soma dos quadrados dos resíduos *RSS*:

- **R²** = 1 − RSS / Σ(yᵢ − ȳ)²
- **AIC** = n·ln(RSS/n) + 2k
- **BIC** = n·ln(RSS/n) + k·ln(n)

Menores valores de AIC/BIC indicam melhor equilíbrio entre qualidade do ajuste
e complexidade. O R² sozinho tende a favorecer modelos com mais parâmetros.

Os erros-padrão dos parâmetros são a raiz da diagonal da matriz de covariância
estimada por `scipy.optimize.curve_fit`.

## Estimativas iniciais

O ajuste não linear depende de bons valores iniciais. O BioFIT os estima a
partir dos próprios dados (`biofit/estimation.py`): platô a partir do máximo
observado, fase lag pelo instante em que a resposta supera 10 % da amplitude,
taxa máxima pela maior derivada numérica e largura de pico pela FWHM.

## Referências

- Zwietering, M. H.; Jongenburger, I.; Rombouts, F. M.; van 't Riet, K. (1990).
  Modeling of the bacterial growth curve. *Applied and Environmental
  Microbiology*, 56(6), 1875–1881.
- Burnham, K. P.; Anderson, D. R. (2002). *Model Selection and Multimodel
  Inference*. 2nd ed. Springer.
