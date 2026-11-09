"""
ETL - Human Development Index (HDI)
Projeto MVP | SSD - UnB | Prof. André Luiz Marques Serrano

Objetivo deste script
----------------------
O arquivo original ("Human Development Index - Full.csv") vem em formato
LARGO (wide): 195 países (linhas) x 880 colunas, sendo 4 colunas de atributos
fixos do país e 876 colunas de indicador-ano (ex.: "Human Development Index
(1990)", "Human Development Index (1991)", ...). Esse formato é ótimo para
leitura humana em planilha, mas é uma anti-prática de modelagem de dados:
- mistura grão de tempo dentro do nome da coluna (não é 1FN);
- qualquer novo ano exige alterar o esquema (schema não é estável);
- não permite relacionar indicador, país e ano como dimensões independentes;
- dificulta o Data Catalog (não dá para catalogar "um indicador", e sim
  876 colunas soltas).

Esta camada de carga (ETL) transforma o dado BRUTO (bronze) no modelo
analítico em ESTRELA (gold), documentando as regras de negócio aplicadas
(exigência da seção "Carga" do trabalho).

Camadas geradas (padrão medallion, compatível com Databricks/Delta Lake):
  bronze/ -> cópia fiel do CSV original, sem nenhuma transformação
  silver/ -> dado "derretido" (melt) para formato longo, tipado e limpo
  gold/   -> modelo em estrela: 1 tabela fato + 3 dimensões, prontas para BI

Como roda no Databricks (resumo - detalhes no README):
  1. Subir "Human Development Index - Full.csv" para um Volume/DBFS
     (ex.: /Volumes/mvp_ssd/bronze/hdi_full.csv).
  2. Importar este script como Notebook (ou rodar via %run).
  3. Trocar os caminhos locais (pathlib) por caminhos dbfs:/ ou Volumes,
     e os df.to_csv(...) por spark.write.format("delta").save(...).
     O código abaixo foi escrito em pandas puro de propósito, para poder
     ser validado localmente antes da migração para PySpark/Databricks.
"""

import re
import pandas as pd
from pathlib import Path

RAW_PATH = Path("/sessions/inspiring-kind-knuth/mnt/uploads/Human Development Index - Full.csv")
OUT_DIR = Path(__file__).resolve().parent.parent / "dados"

ID_COLS = ["ISO3", "Country", "Human Development Groups", "UNDP Developing Regions"]

# Dicionário de unidades/categorias por indicador-base (usado no Data Catalog).
# Regra de negócio: todo indicador que não está listado aqui cai em
# categoria "Outro" e unidade "não informada" - isso é logado no relatório
# de qualidade para garantir rastreabilidade (nenhum dado é descartado
# silenciosamente).
INDICATOR_META = {
    "Human Development Index": ("índice (0-1)", "Síntese"),
    "HDI Rank": ("posição (1-195)", "Síntese"),
    "Inequality-adjusted Human Development Index": ("índice (0-1)", "Síntese"),
    "Planetary pressures-adjusted Human Development Index": ("índice (0-1)", "Síntese"),
    "Coefficient of human inequality": ("percentual (%)", "Desigualdade"),
    "Gender Development Index": ("índice (0-1)", "Gênero"),
    "Gender Inequality Index": ("índice (0-1)", "Gênero"),
    "GDI Group": ("categoria", "Gênero"),
    "GII Rank": ("posição", "Gênero"),
    "HDI female": ("índice (0-1)", "Gênero"),
    "HDI male": ("índice (0-1)", "Gênero"),
    "Life Expectancy at Birth": ("anos", "Saúde"),
    "Life Expectancy at Birth, female": ("anos", "Saúde"),
    "Life Expectancy at Birth, male": ("anos", "Saúde"),
    "Maternal Mortality Ratio (deaths per 100,000 live births)": ("óbitos / 100.000 nascidos vivos", "Saúde"),
    "Adolescent Birth Rate (births per 1,000 women ages 15-19)": ("nascimentos / 1.000 mulheres 15-19", "Saúde"),
    "Expected Years of Schooling": ("anos", "Educação"),
    "Expected Years of Schooling, female": ("anos", "Educação"),
    "Expected Years of Schooling, male": ("anos", "Educação"),
    "Mean Years of Schooling": ("anos", "Educação"),
    "Mean Years of Schooling, female": ("anos", "Educação"),
    "Mean Years of Schooling, male": ("anos", "Educação"),
    "Inequality in eduation": ("percentual (%)", "Desigualdade"),
    "Gross National Income Per Capita": ("US$ PPC", "Renda"),
    "Gross National Income Per Capita, female": ("US$ PPC", "Renda"),
    "Gross National Income Per Capita, male": ("US$ PPC", "Renda"),
    "Inequality in income": ("percentual (%)", "Desigualdade"),
    "Labour force participation rate, female (% ages 15 and older)": ("percentual (%)", "Trabalho"),
    "Labour force participation rate, male (% ages 15 and older)": ("percentual (%)", "Trabalho"),
    "Inequality in life expectancy": ("percentual (%)", "Desigualdade"),
    "Carbon dioxide emissions per capita (production) (tonnes)": ("toneladas/capita", "Meio ambiente"),
    "Material footprint per capita (tonnes)": ("toneladas/capita", "Meio ambiente"),
    "Overall loss (%)": ("percentual (%)", "Síntese"),
    "Difference from HDI rank": ("posições", "Síntese"),
    "Difference from HDI value (%)": ("percentual (%)", "Síntese"),
}


def extrair_bronze() -> pd.DataFrame:
    """Camada BRONZE: leitura fiel do CSV original, sem transformação."""
    df = pd.read_csv(RAW_PATH)
    return df


def transformar_silver(df_bronze: pd.DataFrame) -> pd.DataFrame:
    """
    Camada SILVER: aplica melt (wide -> long).

    Regra de negócio 1: colunas no padrão "<Indicador> (<ano>)" são
    decompostas em (indicador, ano, valor); colunas sem ano (ISO3, Country,
    Human Development Groups, UNDP Developing Regions) tornam-se atributos
    de dimensão do país, repetidos em todas as linhas derretidas daquele
    país (join implícito 1:N).

    Regra de negócio 2: linhas com valor nulo são mantidas (não são
    descartadas) para que o relatório de qualidade consiga medir
    completude real por indicador/ano - descartar aqui esconderia o
    problema em vez de documentá-lo.
    """
    value_cols = [c for c in df_bronze.columns if c not in ID_COLS]
    df_long = df_bronze.melt(
        id_vars=ID_COLS, value_vars=value_cols, var_name="coluna_origem", value_name="valor"
    )

    pattern = re.compile(r"^(.*) \((\d{4})\)$")

    def split_col(c):
        m = pattern.match(c)
        if m:
            return m.group(1), int(m.group(2))
        return c, None  # indicador sem ano explícito (não deveria ocorrer; logado)

    parsed = df_long["coluna_origem"].apply(split_col)
    df_long["indicador"] = parsed.apply(lambda t: t[0])
    df_long["ano"] = parsed.apply(lambda t: t[1])
    df_long = df_long.drop(columns=["coluna_origem"])

    # Regra de negócio 3: valor deve ser numérico; strings residuais (ex.: "..",
    # presentes na fonte original do PNUD para "sem dado") são convertidas em NaN.
    df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")

    return df_long


def modelar_gold(df_silver: pd.DataFrame):
    """
    Camada GOLD: modelo em estrela.

    dim_pais(iso3 PK, pais, grupo_hdi, regiao_undp)
    dim_indicador(indicador_id PK, indicador, unidade, categoria)
    dim_ano(ano PK)
    fato_indicadores(iso3 FK, indicador_id FK, ano FK, valor)
    """
    dim_pais = (
        df_silver[["ISO3", "Country", "Human Development Groups", "UNDP Developing Regions"]]
        .drop_duplicates()
        .rename(columns={
            "ISO3": "iso3", "Country": "pais",
            "Human Development Groups": "grupo_hdi",
            "UNDP Developing Regions": "regiao_undp",
        })
        .reset_index(drop=True)
    )

    indicadores = sorted(df_silver["indicador"].dropna().unique())
    dim_indicador = pd.DataFrame({"indicador": indicadores})
    dim_indicador["indicador_id"] = range(1, len(dim_indicador) + 1)
    dim_indicador["unidade"] = dim_indicador["indicador"].map(lambda i: INDICATOR_META.get(i, ("não informada", "Outro"))[0])
    dim_indicador["categoria"] = dim_indicador["indicador"].map(lambda i: INDICATOR_META.get(i, ("não informada", "Outro"))[1])
    dim_indicador = dim_indicador[["indicador_id", "indicador", "unidade", "categoria"]]

    dim_ano = pd.DataFrame({"ano": sorted(df_silver["ano"].dropna().unique().astype(int))})

    fato = df_silver.merge(dim_indicador[["indicador", "indicador_id"]], on="indicador", how="left")
    fato = fato.rename(columns={"ISO3": "iso3"})[["iso3", "indicador_id", "ano", "valor"]]
    fato = fato.dropna(subset=["ano"])
    fato["ano"] = fato["ano"].astype(int)

    return dim_pais, dim_indicador, dim_ano, fato


def main():
    for sub in ["bronze", "silver", "gold"]:
        (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)

    bronze = extrair_bronze()
    bronze.to_csv(OUT_DIR / "bronze" / "hdi_full_raw.csv", index=False)

    silver = transformar_silver(bronze)
    silver.to_csv(OUT_DIR / "silver" / "hdi_long.csv", index=False)

    dim_pais, dim_indicador, dim_ano, fato = modelar_gold(silver)
    dim_pais.to_csv(OUT_DIR / "gold" / "dim_pais.csv", index=False)
    dim_indicador.to_csv(OUT_DIR / "gold" / "dim_indicador.csv", index=False)
    dim_ano.to_csv(OUT_DIR / "gold" / "dim_ano.csv", index=False)
    fato.to_csv(OUT_DIR / "gold" / "fato_indicadores.csv", index=False)

    print("Bronze:", bronze.shape)
    print("Silver (long):", silver.shape)
    print("Gold -> dim_pais:", dim_pais.shape, "| dim_indicador:", dim_indicador.shape,
          "| dim_ano:", dim_ano.shape, "| fato_indicadores:", fato.shape)


if __name__ == "__main__":
    main()
