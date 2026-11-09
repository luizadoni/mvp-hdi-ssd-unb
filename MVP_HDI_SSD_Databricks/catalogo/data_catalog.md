# Data Catalog — Projeto MVP HDI (SSD/UnB)

Catálogo de dados do modelo analítico em estrela gerado por
`scripts/etl_hdi_star_schema.py` a partir da fonte bruta
`Human Development Index - Full.csv` (PNUD, Human Development Report Office).

Fonte original: UNDP Human Development Reports — https://hdr.undp.org/data-center
Licença da fonte: dados públicos do PNUD, uso livre para fins acadêmicos com citação da fonte.

## Linhagem (lineage)

```
Human Development Index - Full.csv  (bronze — fidelidade ao arquivo da fonte)
        │  scripts/etl_hdi_star_schema.py :: extrair_bronze()
        ▼
dados/bronze/hdi_full_raw.csv
        │  :: transformar_silver()  — melt wide→long, parse "<indicador> (<ano>)", cast numérico
        ▼
dados/silver/hdi_long.csv   (grão: 1 linha = 1 país x 1 indicador x 1 ano)
        │  :: modelar_gold()  — split em fato + 3 dimensões
        ▼
dados/gold/dim_pais.csv | dim_indicador.csv | dim_ano.csv | fato_indicadores.csv
        │  scripts/qualidade_dados.py
        ▼
catalogo/relatorio_qualidade_dados.md  (evidência de qualidade, 6 dimensões)
```

## Modelo em estrela

```
                dim_ano (32)
                     │ ano (PK)
                     │
dim_pais (195) ──┐   │   ┌── dim_indicador (35)
  iso3 (PK)       │  │   │     indicador_id (PK)
  pais            │  │   │     indicador
  grupo_hdi        ▼  ▼  ▼     unidade
  regiao_undp   fato_indicadores     categoria
                  iso3 (FK)
                  indicador_id (FK)
                  ano (FK)
                  valor
```

Grão da tabela fato: **1 linha = 1 valor de 1 indicador, de 1 país, em 1 ano.**
170.820 linhas (195 países × 35 indicadores × ~25 anos efetivos com dado, de 32 anos no calendário 1990-2021).

## Dicionário de dados

### `dim_pais` (195 linhas)

| Atributo | Tipo | Domínio | Descrição |
|---|---|---|---|
| `iso3` (PK) | string(3) | 195 códigos ISO-3166 alfa-3 em maiúsculas | Identificador único do país |
| `pais` | string | nome do país em inglês, conforme PNUD | Nome descritivo |
| `grupo_hdi` | categórico | {Low, Medium, High, Very High, NaN} | Grupo de desenvolvimento humano 2021; 4 países sem classificação (ver relatório de qualidade) |
| `regiao_undp` | categórico | regiões PNUD (ex.: SSA, LAC, EAP, SA, ECA, AS, NaN) | Agrupamento regional do PNUD |

### `dim_indicador` (35 linhas)

| Atributo | Tipo | Domínio | Descrição |
|---|---|---|---|
| `indicador_id` (PK) | inteiro | 1–35 | Chave substituta gerada no ETL |
| `indicador` | string | nome original do indicador no CSV fonte | Rótulo de negócio |
| `unidade` | string | ver tabela de categorias abaixo | Unidade de medida |
| `categoria` | categórico | {Síntese, Saúde, Educação, Renda, Gênero, Desigualdade, Trabalho, Meio ambiente} | Agrupamento temático definido nesta carga (regra de negócio documentada em `INDICATOR_META`) |

### `dim_ano` (32 linhas)

| Atributo | Tipo | Domínio | Descrição |
|---|---|---|---|
| `ano` (PK) | inteiro | 1990–2021 | Ano civil do dado reportado pelo PNUD |

### `fato_indicadores` (170.820 linhas)

| Atributo | Tipo | Domínio | Descrição |
|---|---|---|---|
| `iso3` (FK → dim_pais) | string(3) | — | País do valor |
| `indicador_id` (FK → dim_indicador) | inteiro | — | Indicador do valor |
| `ano` (FK → dim_ano) | inteiro | — | Ano do valor |
| `valor` | float | varia por indicador (ver `unidade`) | Métrica observada; 11,7% nulo (ver relatório de qualidade, seção 1) |

## Categorias de indicador e unidades

| Categoria | Qtde. indicadores | Exemplos | Unidade típica |
|---|---|---|---|
| Síntese | 7 | Human Development Index, HDI Rank, Overall loss (%) | índice (0-1), posição, % |
| Saúde | 5 | Life Expectancy at Birth, Maternal Mortality Ratio | anos, óbitos/100k |
| Educação | 6 | Mean/Expected Years of Schooling | anos |
| Renda | 3 | Gross National Income Per Capita | US$ PPC |
| Gênero | 6 | Gender Development Index, HDI female/male | índice (0-1), posição |
| Desigualdade | 4 | Coefficient of human inequality, Inequality in income | % |
| Trabalho | 2 | Labour force participation rate | % |
| Meio ambiente | 2 | CO₂ emissions per capita, Material footprint | toneladas/capita |

## Regras de negócio aplicadas na carga (resumo — detalhe no código)

1. Colunas no padrão `"<Indicador> (<ano>)"` são decompostas em indicador + ano; as 4 colunas restantes tornam-se atributos fixos de `dim_pais`.
2. Valores nulos **não são descartados** no silver — são preservados para que a completude real apareça no relatório de qualidade (descartar esconderia o problema).
3. Qualquer indicador fora do dicionário `INDICATOR_META` cairia em categoria "Outro"/"não informada" (não ocorreu nesta carga — os 35 indicadores da fonte estão todos mapeados).
4. `indicador_id` é uma chave substituta (surrogate key) gerada no ETL, não existe na fonte.
