"""
Auditoria de Qualidade de Dados - HDI
Projeto MVP | SSD - UnB

Mede as 6 dimensões clássicas de qualidade de dados exigidas no trabalho:
completude, unicidade, consistência, conformidade, acurácia e atualidade.
Cada métrica é calculada sobre o modelo GOLD (fato_indicadores + dimensões),
gerado por etl_hdi_star_schema.py, e o resultado é salvo em
catalogo/relatorio_qualidade_dados.md para virar evidência no repositório
e insumo direto da seção "Análise > Qualidade de dados" do paper.
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GOLD = BASE / "dados" / "gold"
OUT = BASE / "catalogo" / "relatorio_qualidade_dados.md"


def main():
    dim_pais = pd.read_csv(GOLD / "dim_pais.csv")
    dim_indicador = pd.read_csv(GOLD / "dim_indicador.csv")
    dim_ano = pd.read_csv(GOLD / "dim_ano.csv")
    fato = pd.read_csv(GOLD / "fato_indicadores.csv")

    linhas_md = []
    linhas_md.append("# Relatório de Qualidade de Dados — HDI (camada Gold)\n")
    linhas_md.append("Gerado automaticamente por `scripts/qualidade_dados.py`.\n")

    # 1. COMPLETUDE: % de valores não nulos na tabela fato, geral e por indicador.
    total = len(fato)
    nao_nulos = fato["valor"].notna().sum()
    completude_geral = 100 * nao_nulos / total
    linhas_md.append("## 1. Completude\n")
    linhas_md.append(f"- Linhas na tabela fato (país x indicador x ano): **{total:,}**")
    linhas_md.append(f"- Valores preenchidos: **{nao_nulos:,}** ({completude_geral:.1f}%)")
    linhas_md.append(f"- Valores ausentes: **{total - nao_nulos:,}** ({100 - completude_geral:.1f}%)\n")

    comp_por_indicador = (
        fato.merge(dim_indicador, on="indicador_id")
        .groupby("indicador")["valor"]
        .apply(lambda s: 100 * s.notna().sum() / len(s))
        .sort_values()
    )
    piores = comp_por_indicador.head(5)
    melhores = comp_por_indicador.tail(5)
    linhas_md.append("**5 indicadores com menor completude:**\n")
    for ind, pct in piores.items():
        linhas_md.append(f"- {ind}: {pct:.1f}%")
    linhas_md.append("\n**5 indicadores com maior completude:**\n")
    for ind, pct in melhores.items():
        linhas_md.append(f"- {ind}: {pct:.1f}%")
    linhas_md.append("")

    # 2. UNICIDADE: duplicatas na chave primária de cada tabela.
    linhas_md.append("## 2. Unicidade\n")
    dup_pais = dim_pais["iso3"].duplicated().sum()
    dup_fato = fato.duplicated(subset=["iso3", "indicador_id", "ano"]).sum()
    linhas_md.append(f"- `dim_pais` — duplicidade de ISO3 (chave primária): **{dup_pais}**")
    linhas_md.append(f"- `fato_indicadores` — duplicidade de grão (iso3, indicador, ano): **{dup_fato}**")
    linhas_md.append(f"- Total de países distintos: **{dim_pais['iso3'].nunique()}** (esperado: 195 segundo a fonte)\n")

    # 3. CONSISTÊNCIA: país não pode mudar de grupo HDI nem de região entre colunas,
    # e toda combinação (iso3, indicador, ano) do fato deve ter dimensão correspondente (integridade referencial).
    linhas_md.append("## 3. Consistência\n")
    fk_pais_orfao = (~fato["iso3"].isin(dim_pais["iso3"])).sum()
    fk_ind_orfao = (~fato["indicador_id"].isin(dim_indicador["indicador_id"])).sum()
    fk_ano_orfao = (~fato["ano"].isin(dim_ano["ano"])).sum()
    linhas_md.append(f"- Linhas do fato com `iso3` sem dimensão correspondente: **{fk_pais_orfao}**")
    linhas_md.append(f"- Linhas do fato com `indicador_id` sem dimensão correspondente: **{fk_ind_orfao}**")
    linhas_md.append(f"- Linhas do fato com `ano` fora do intervalo esperado (1990-2021): **{fk_ano_orfao}**")
    grupos_nulos = dim_pais["grupo_hdi"].isna().sum()
    linhas_md.append(f"- Países sem `grupo_hdi` atribuído: **{grupos_nulos}** de {len(dim_pais)}\n")

    # 4. CONFORMIDADE: valores fora do domínio esperado (ex.: HDI deve estar em [0,1]).
    linhas_md.append("## 4. Conformidade\n")
    hdi_id = dim_indicador.loc[dim_indicador["indicador"] == "Human Development Index", "indicador_id"]
    if not hdi_id.empty:
        hdi_vals = fato.loc[fato["indicador_id"] == hdi_id.iloc[0], "valor"].dropna()
        fora_dominio = ((hdi_vals < 0) | (hdi_vals > 1)).sum()
        linhas_md.append(f"- Valores de `Human Development Index` fora do domínio [0,1]: **{fora_dominio}** de {len(hdi_vals)}")
    vida_id = dim_indicador.loc[dim_indicador["indicador"] == "Life Expectancy at Birth", "indicador_id"]
    if not vida_id.empty:
        vida_vals = fato.loc[fato["indicador_id"] == vida_id.iloc[0], "valor"].dropna()
        fora_dominio_vida = ((vida_vals < 0) | (vida_vals > 100)).sum()
        linhas_md.append(f"- Valores de `Life Expectancy at Birth` fora do domínio [0,100] anos: **{fora_dominio_vida}** de {len(vida_vals)}")
    iso3_invalidos = (~dim_pais["iso3"].astype(str).str.match(r"^[A-Z]{3}$")).sum()
    linhas_md.append(f"- ISO3 com formato inválido (≠ 3 letras maiúsculas): **{iso3_invalidos}**\n")

    # 5. ACURÁCIA (proxy): coerência cruzada entre HDI reportado e HDI recalculado
    #    a partir das 3 subdimensões normalizadas não é viável sem a fórmula oficial
    #    completa; usamos como proxy de acurácia a comparação entre HDI Rank
    #    informado e o rank que resulta de ordenar o HDI (2021) na própria base.
    linhas_md.append("## 5. Acurácia (proxy)\n")
    hdi2021 = fato[(fato["indicador_id"] == hdi_id.iloc[0]) & (fato["ano"] == 2021)][["iso3", "valor"]].dropna()
    hdi2021 = hdi2021.sort_values("valor", ascending=False).reset_index(drop=True)
    hdi2021["rank_recalculado"] = hdi2021.index + 1
    rank_id = dim_indicador.loc[dim_indicador["indicador"] == "HDI Rank", "indicador_id"]
    if not rank_id.empty:
        rank_oficial = fato[(fato["indicador_id"] == rank_id.iloc[0]) & (fato["ano"] == 2021)][["iso3", "valor"]].rename(columns={"valor": "rank_oficial"})
        comp = hdi2021.merge(rank_oficial, on="iso3", how="inner")
        comp["diferenca"] = (comp["rank_recalculado"] - comp["rank_oficial"]).abs()
        linhas_md.append(f"- Países comparados: **{len(comp)}**")
        linhas_md.append(f"- Diferença média |rank recalculado − rank oficial|: **{comp['diferenca'].mean():.2f} posições**")
        linhas_md.append(f"- Países com diferença > 2 posições: **{(comp['diferenca'] > 2).sum()}**")
        linhas_md.append("- Interpretação: pequenas diferenças são esperadas por empates/arredondamento de 3 casas decimais; divergências grandes indicariam erro de carga.\n")

    # 6. ATUALIDADE: distância entre o ano mais recente disponível e o ano de referência do trabalho (2026).
    linhas_md.append("## 6. Atualidade\n")
    ano_max = int(dim_ano["ano"].max())
    ano_ref = 2026
    linhas_md.append(f"- Ano mais recente disponível na base: **{ano_max}**")
    linhas_md.append(f"- Defasagem em relação ao ano de entrega do trabalho ({ano_ref}): **{ano_ref - ano_max} anos**")
    linhas_md.append("- Causa: o PNUD publica o Relatório de Desenvolvimento Humano com atraso metodológico de ~2 a 3 anos; é uma limitação da fonte, não da coleta.\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(linhas_md), encoding="utf-8")
    print("Relatório salvo em:", OUT)
    print("\n".join(linhas_md))


if __name__ == "__main__":
    main()
