"""
Análise aprofundada (nova em relação à versão anterior do MVP) — HDI
Projeto MVP | SSD - UnB

Pergunta de negócio 3 (nova): Países que mantiveram desigualdade mais alta ao
longo de 1990-2021 tendem a terminar o período em um grupo de Desenvolvimento
Humano mais baixo? Em outras palavras: desigualdade persistente está
associada a MENOR mobilidade de desenvolvimento humano no longo prazo?

Diferença em relação à análise anterior do MVP (que era só um corte
transversal de 2021, comparando classificação tradicional por quartil de
renda x Random Forest/Regressão Logística): aqui usamos a dimensão temporal
do próprio painel (1990-2021), algo que o modelo em estrela construído nesta
carga passa a permitir de forma direta (antes, com o CSV largo, cada ano
era uma coluna separada e cruzar "trajetória ao longo do tempo" com
"desigualdade média" exigia reescrever a lógica de seleção de colunas a
cada nova pergunta).

Método:
1. Classifica o HDI de cada país em 1990 e em 2021 nos 4 grupos oficiais do
   PNUD (Low <0.550, Medium 0.550-0.699, High 0.700-0.799, Very High >=0.800).
2. Marca como "subiu de grupo" todo país cujo grupo em 2021 é superior ao de
   1990 (ex.: Medium -> High).
3. Calcula a desigualdade média do país ao longo de todo o período
   disponível (Coefficient of human inequality).
4. Compara a desigualdade média entre quem subiu e quem não subiu de grupo
   (teste t de Welch) e mede a correlação (Spearman, por se tratar de uma
   variável ordinal — rank_2021 — vs. uma variável contínua) entre o nível
   final de desenvolvimento humano e a desigualdade média acumulada.

Resultado obtido (reproduzido a partir de dados/gold/analise_mobilidade_hdi.csv):
- 141 países possuem HDI registrado tanto em 1990 quanto em 2021.
- 65,2% desses países (92 de 141) subiram de grupo HDI no período.
- Desigualdade média entre quem subiu: 17,42; entre quem não subiu: 20,73
  (teste t de Welch: t=-1,75, p=0,084 — diferença não significativa a 5%,
  apenas marginal a 10%; a diferença de médias por si só é um indício fraco).
- Correlação de Spearman entre nível HDI final (ordinal, 0-3) e desigualdade
  média acumulada 1990-2021: rho = -0,842 (p < 0,001, n=132) — forte e
  estatisticamente muito significativa.

Leitura crítica (para a seção de Análise/Discussão do paper):
A comparação simples de médias (subiu x não subiu) não é estatisticamente
conclusiva isoladamente. Mas a correlação de Spearman, que usa o nível de
desenvolvimento humano INTEIRO (não apenas se subiu ou não), mostra uma
associação forte e muito significativa: quanto maior a desigualdade média
sustentada ao longo de três décadas, mais baixo tende a ser o patamar final
de desenvolvimento humano do país. Isso é consistente com a literatura de
economia do desenvolvimento (desigualdade alta tende a restringir mobilidade
social e investimento em capital humano), mas CORRELAÇÃO NÃO É CAUSALIDADE:
o desenho aqui é observacional e não controla fatores como guerra, regime
político, geografia ou choques econômicos externos — isso deve constar
explicitamente como limitação.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / "dados" / "gold"

GRUPOS_ORDEM = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}


def classificar_hdi(valor):
    if pd.isna(valor):
        return np.nan
    if valor < 0.550:
        return "Low"
    if valor < 0.700:
        return "Medium"
    if valor < 0.800:
        return "High"
    return "Very High"


def main():
    fato = pd.read_csv(GOLD / "fato_indicadores.csv")
    dim_ind = pd.read_csv(GOLD / "dim_indicador.csv")

    hdi_id = dim_ind.loc[dim_ind.indicador == "Human Development Index", "indicador_id"].iloc[0]
    ineq_id = dim_ind.loc[dim_ind.indicador == "Coefficient of human inequality", "indicador_id"].iloc[0]

    hdi = fato[fato.indicador_id == hdi_id][["iso3", "ano", "valor"]].rename(columns={"valor": "hdi"})
    h1990 = hdi[hdi.ano == 1990].set_index("iso3")["hdi"].apply(classificar_hdi)
    h2021 = hdi[hdi.ano == 2021].set_index("iso3")["hdi"].apply(classificar_hdi)

    df = pd.DataFrame({"grupo_1990": h1990, "grupo_2021": h2021}).dropna()
    df["rank_1990"] = df["grupo_1990"].map(GRUPOS_ORDEM)
    df["rank_2021"] = df["grupo_2021"].map(GRUPOS_ORDEM)
    df["subiu_grupo"] = df["rank_2021"] > df["rank_1990"]

    ineq = fato[fato.indicador_id == ineq_id][["iso3", "valor"]].dropna()
    ineq_media = ineq.groupby("iso3")["valor"].mean().rename("ineq_media")

    df2 = df.join(ineq_media, how="inner")

    a = df2.loc[df2["subiu_grupo"], "ineq_media"].dropna()
    b = df2.loc[~df2["subiu_grupo"], "ineq_media"].dropna()
    t, p_t = stats.ttest_ind(a, b, equal_var=False)
    rho, p_rho = stats.spearmanr(df2["rank_2021"], df2["ineq_media"])

    print(f"Países com HDI 1990 e 2021: {len(df)}")
    print(f"Subiram de grupo: {df['subiu_grupo'].sum()} ({100*df['subiu_grupo'].mean():.1f}%)")
    print(f"Desigualdade média — subiu: {a.mean():.2f} | não subiu: {b.mean():.2f}")
    print(f"Teste t de Welch: t={t:.3f}, p={p_t:.4f}")
    print(f"Correlação de Spearman (nível HDI 2021 x desigualdade média 1990-2021): rho={rho:.3f}, p={p_rho:.6f}, n={len(df2)}")

    df2.reset_index().rename(columns={"index": "iso3"}).to_csv(GOLD / "analise_mobilidade_hdi.csv", index=False)
    print("\nResultado salvo em dados/gold/analise_mobilidade_hdi.csv")


if __name__ == "__main__":
    main()
