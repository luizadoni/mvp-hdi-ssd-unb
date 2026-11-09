# Relatório de Qualidade de Dados — HDI (camada Gold)

Gerado automaticamente por `scripts/qualidade_dados.py`.

## 1. Completude

- Linhas na tabela fato (país x indicador x ano): **170,820**
- Valores preenchidos: **150,817** (88.3%)
- Valores ausentes: **20,003** (11.7%)

**5 indicadores com menor completude:**

- Inequality-adjusted Human Development Index: 74.2%
- Coefficient of human inequality: 74.2%
- Overall loss (%): 74.2%
- Planetary pressures-adjusted Human Development Index: 75.0%
- Difference from HDI value (%): 75.0%

**5 indicadores com maior completude:**

- Life Expectancy at Birth, female: 100.0%
- Life Expectancy at Birth: 100.0%
- Inequality in life expectancy: 100.0%
- Life Expectancy at Birth, male: 100.0%
- Adolescent Birth Rate (births per 1,000 women ages 15-19): 100.0%

## 2. Unicidade

- `dim_pais` — duplicidade de ISO3 (chave primária): **0**
- `fato_indicadores` — duplicidade de grão (iso3, indicador, ano): **0**
- Total de países distintos: **195** (esperado: 195 segundo a fonte)

## 3. Consistência

- Linhas do fato com `iso3` sem dimensão correspondente: **0**
- Linhas do fato com `indicador_id` sem dimensão correspondente: **0**
- Linhas do fato com `ano` fora do intervalo esperado (1990-2021): **0**
- Países sem `grupo_hdi` atribuído: **4** de 195

## 4. Conformidade

- Valores de `Human Development Index` fora do domínio [0,1]: **0** de 5571
- Valores de `Life Expectancy at Birth` fora do domínio [0,100] anos: **0** de 6240
- ISO3 com formato inválido (≠ 3 letras maiúsculas): **0**

## 5. Acurácia (proxy)

- Países comparados: **191**
- Diferença média |rank recalculado − rank oficial|: **0.19 posições**
- Países com diferença > 2 posições: **1**
- Interpretação: pequenas diferenças são esperadas por empates/arredondamento de 3 casas decimais; divergências grandes indicariam erro de carga.

## 6. Atualidade

- Ano mais recente disponível na base: **2021**
- Defasagem em relação ao ano de entrega do trabalho (2026): **5 anos**
- Causa: o PNUD publica o Relatório de Desenvolvimento Humano com atraso metodológico de ~2 a 3 anos; é uma limitação da fonte, não da coleta.
