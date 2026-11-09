# MVP — Desenvolvimento Humano: desigualdade, previsão e mobilidade (1990–2021)

**Disciplina:** Sistemas de Suporte à Decisão (SSD) — Departamento de Engenharia de Produção, UnB
**Professor:** André Luiz Marques Serrano
**Autora:** Luíza Doniak
**Plataforma de nuvem:** Databricks (Community/free tier) — ver `catalogo/guia_databricks.md` para evidências de execução
**Base de dados:** Human Development Index — Full (UNDP Human Development Report Office), 195 países, painel 1990–2021

---

## 1. Objetivo

O MVP testa a hipótese de que **indicadores estruturais de desenvolvimento humano — especialmente a desigualdade — carregam informação suficiente para (a) classificar o estágio de desenvolvimento de um país melhor do que um critério tradicional de renda, e (b) explicar por que alguns países avançam de patamar de desenvolvimento humano ao longo do tempo e outros não.**

### Perguntas de negócio

| # | Pergunta | Tipo | Onde é respondida |
|---|---|---|---|
| 1 | É possível prever o Grupo de Desenvolvimento Humano (Low/Medium/High/Very High) de um país em 2021 com desempenho superior a uma regra tradicional baseada em quartil de renda? | Classificação (corte transversal) | `notebooks/Projeto_HDI_IA_vs_Tradicional.ipynb` |
| 2 | Quais indicadores (saúde, educação, renda, desigualdade) mais pesam nessa classificação? | Explicabilidade do modelo | idem (feature importance, Random Forest) |
| 3 | Desigualdade persistente ao longo de 1990–2021 está associada a um patamar final de desenvolvimento humano mais baixo em 2021? | Análise longitudinal (nova nesta versão) | `scripts/analise_mobilidade_desigualdade.py` |
| 4 | Os dados têm qualidade suficiente (completude, consistência, conformidade) para sustentar as respostas acima? | Qualidade de dados | `catalogo/relatorio_qualidade_dados.md` |

As perguntas 1 e 2 foram atingidas com dado de corte transversal (2021). A pergunta 3 é a extensão feita nesta entrega, habilitada pelo modelo em estrela (ver seção 3), que usa a dimensão temporal do painel — algo inviável de explorar de forma direta a partir do CSV original em formato largo (um ano = uma coluna).

---

## 2. Busca e coleta

- **Fonte:** UNDP Human Development Reports — https://hdr.undp.org/data-center (dados públicos, uso livre para fins acadêmicos com citação da fonte).
- **Formato original:** CSV único, 195 linhas (países) x 880 colunas (4 atributos fixos + 35 indicadores x ~25 anos efetivos cada, calendário 1990–2021).
- **Data da coleta:** conforme registrado no notebook original do projeto (download via Kaggle, espelhando a base do PNUD).
- **Licença:** dados públicos do PNUD. Sem restrição de redistribuição para fins acadêmicos — por isso o CSV bruto é versionado em `dados/bronze/` (ver seção 4 sobre ética e licenciamento).
- **Persistência na nuvem:** os arquivos `dados/bronze`, `dados/silver` e `dados/gold` foram carregados em Volumes do Databricks (`/Volumes/mvp_ssd/...`) — evidência em `evidencias/`.

---

## 3. Modelagem

Optou-se por um **modelo em estrela** (star schema), adequado porque há uma métrica clara (`valor` de um indicador) observada em múltiplas dimensões (país, indicador, ano) — o caso clássico de fato + dimensões.

```
dim_pais (195) ──┐                    ┌── dim_indicador (35)
  iso3 (PK)        │                  │     indicador_id (PK)
  pais             │                  │     indicador, unidade, categoria
  grupo_hdi        ▼                  ▼
  regiao_undp   fato_indicadores (170.820 linhas)
                  iso3 (FK) · indicador_id (FK) · ano (FK) · valor
                      ▲
                      │
                 dim_ano (32) — ano (PK), 1990–2021
```

Grão da fato: **1 linha = 1 valor de 1 indicador, de 1 país, em 1 ano.**

O **Catálogo de Dados completo** (atributo, tipo, domínio, obrigatoriedade, linhagem) está em [`catalogo/data_catalog.md`](catalogo/data_catalog.md).

---

## 4. Carga (ETL)

Pipeline implementado em `scripts/etl_hdi_star_schema.py`, em três camadas (padrão medallion, compatível com Delta Lake/Databricks):

1. **Bronze** — cópia fiel do CSV original, sem transformação (auditoria de proveniência).
2. **Silver** — `melt` (wide → long): cada coluna `"<Indicador> (<ano>)"` é decomposta em `(indicador, ano, valor)`. Valores ausentes são **preservados** (não descartados), para que a completude real apareça na auditoria de qualidade.
3. **Gold** — modelo em estrela final (fato + 3 dimensões), pronto para consulta analítica/BI.

**Regras de negócio documentadas no código** (ver docstring do script):
- parsing de nome de coluna via regex `"<indicador> (<ano>)"`;
- padronização de `indicador_id` como chave substituta;
- qualquer indicador fora do dicionário de metadados cairia em categoria "Outro" (não ocorreu — os 35 indicadores da fonte foram todos mapeados);
- valores textuais residuais (ex.: ausência de dado) convertidos para nulo numérico, nunca descartados silenciosamente.

No Databricks, o mesmo pipeline roda substituindo `pandas.read_csv`/`to_csv` por `spark.read.csv(...)` e `.write.format("delta").saveAsTable(...)` — ver `catalogo/guia_databricks.md`.

---

## 5. Análise

### 5.a Qualidade de dados

Relatório completo com números reais, por dimensão (completude, unicidade, consistência, conformidade, acurácia, atualidade), em [`catalogo/relatorio_qualidade_dados.md`](catalogo/relatorio_qualidade_dados.md). Resumo:

| Dimensão | Resultado |
|---|---|
| Completude | 88,3% dos 170.820 valores preenchidos (11,7% ausentes, concentrados em indicadores derivados como "Inequality-adjusted HDI", presentes só a partir de ~2010) |
| Unicidade | 0 duplicatas de chave em `dim_pais` e `fato_indicadores`; 195 países únicos, como esperado |
| Consistência | 0 linhas órfãs (integridade referencial 100% entre fato e dimensões); 4 países sem `grupo_hdi` atribuído |
| Conformidade | 0 valores de HDI fora de [0,1]; 0 valores de expectativa de vida fora de [0,100]; 0 ISO3 em formato inválido |
| Acurácia (proxy) | Rank recalculado a partir do HDI 2021 diverge do rank oficial do PNUD em média 0,19 posição (191 países comparados) — divergência desprezível, por arredondamento |
| Atualidade | Último ano disponível: 2021 (defasagem de 5 anos frente a 2026, por atraso metodológico de publicação do PNUD — limitação da fonte, não da coleta) |

**Conclusão de qualidade:** a base é confiável para sustentar as respostas às perguntas 1–3. A única ressalva relevante é a completude menor (~74–75%) nos índices "ajustados" (desigualdade, pressão planetária), que não são usados como variável principal nas respostas abaixo.

### 5.b Solução do problema

**Pergunta 1 e 2 — Classificação tradicional vs. Machine Learning (corte 2021).**
Reaproveitado e mantido do MVP original (`notebooks/Projeto_HDI_IA_vs_Tradicional.ipynb`):
- Classificação tradicional (regra de quartil de renda): **69,8%** de acurácia.
- Random Forest (validação cruzada 5-fold estratificada): **86,8%**; no holdout de 46 países: **89,1%**.
- Regressão Logística: **84,8%** no holdout.
- Ganho de ≈17 pontos percentuais do melhor modelo de ML sobre a regra tradicional.
- Variáveis mais importantes (Random Forest): renda per capita, anos esperados de escolaridade e expectativa de vida — excluindo-se deliberadamente HDI e HDI Rank das variáveis preditoras, por serem a origem direta do rótulo (vazamento de dados).

**Pergunta 3 — Mobilidade de grupo HDI x desigualdade acumulada (1990–2021), nova nesta versão.**
Script: `scripts/analise_mobilidade_desigualdade.py`.
- 141 países com HDI registrado em 1990 e 2021; **65,2% (92 países) subiram de grupo HDI** no período.
- Desigualdade média (Coefficient of human inequality) foi menor entre os países que subiram de grupo (17,42) do que entre os que não subiram (20,73) — diferença apenas **marginal** (teste t de Welch: p=0,084, não significativa a 5%).
- Mais robusto: a **correlação de Spearman entre o nível final de desenvolvimento humano (2021) e a desigualdade média sustentada ao longo de 1990–2021 é de ρ = −0,842 (p < 0,001, n=132)** — forte e estatisticamente muito significativa.
- **Discussão:** países que mantiveram desigualdade mais alta por décadas tendem a terminar em patamares de desenvolvimento humano mais baixos. Isso é compatível com a literatura de economia do desenvolvimento (desigualdade alta tende a restringir investimento em capital humano e mobilidade social), mas o desenho é observacional: não há controle por guerra, regime político, geografia ou choques externos, de modo que a relação deve ser lida como associação, não como causalidade comprovada.

---

## 6. Ética, licenciamento e proteção de dados

Ver detalhamento em [`catalogo/etica_licenciamento_lgpd.md`](catalogo/etica_licenciamento_lgpd.md). Resumo: dado público e agregado por país (sem dado pessoal identificável), licença do PNUD permite uso e redistribuição acadêmica, nenhuma coleta por *web scraping* foi necessária, não há dado de empresa envolvido — portanto a LGPD não se aplica à base em si, mas o cuidado está documentado por completude.

---

## 7. Autoavaliação

**1) Quais das perguntas de negócio formuladas no objetivo foram respondidas e quais não foram? Por quê?**
As quatro perguntas foram respondidas. A pergunta 3 (mobilidade x desigualdade) é a mais frágil estatisticamente na comparação de médias simples (p=0,084), mas ganhou robustez ao ser reformulada como correlação ordinal (Spearman, p<0,001) — o que, em si, é um aprendizado metodológico: a forma de operacionalizar uma pergunta de negócio (grupo binário "subiu/não subiu" vs. nível ordinal contínuo) muda a conclusão estatística.

**2) Que limitações dos dados condicionaram os resultados obtidos?**
Defasagem de 5 anos (último dado é de 2021); completude mais baixa (~74-75%) nos índices ajustados por desigualdade/sustentabilidade, o que limitou o uso desses índices como variável principal; dado é agregado por país, não captura desigualdade intra-país (regiões, grupos sociais) nem choques recentes (pandemia, conflitos pós-2021).

**3) Quais decisões técnicas você tomaria de outra forma se recomeçasse o trabalho?**
Modelaria o esquema em estrela desde o início do projeto (e não como retrofit), o que teria liberado a análise longitudinal (pergunta 3) desde a primeira versão. Também incluiria desde o início uma camada de teste automatizado (ex.: `pytest` validando domínios do Catálogo de Dados contra o conteúdo real da tabela fato a cada execução do ETL), em vez de validar qualidade só ao final.

**4) Que extensões seriam necessárias para transformar este MVP em uma solução de uso contínuo?**
Agendamento do pipeline (Databricks Jobs) para reexecutar a carga quando o PNUD publicar nova edição anual; adicionar fontes complementares (ex.: Banco Mundial, OCDE) para reduzir a defasagem de atualidade; evoluir o teste de hipótese causal da pergunta 3 para um desenho quase-experimental (ex.: painel com efeitos fixos por país, controlando choques comuns por ano) em vez de correlação simples; expor os resultados via dashboard (Databricks SQL ou Power BI) para consulta contínua por não-programadores.

---

## 8. Estrutura do repositório

```
README.md                                 este documento
/notebooks
  Projeto_HDI_IA_vs_Tradicional.ipynb     classificação ML x tradicional (perguntas 1 e 2)
/scripts
  etl_hdi_star_schema.py                  ETL bronze/silver/gold (carga)
  qualidade_dados.py                      auditoria de qualidade (6 dimensões)
  analise_mobilidade_desigualdade.py      análise longitudinal nova (pergunta 3)
/catalogo
  data_catalog.md                         catálogo de dados + linhagem
  relatorio_qualidade_dados.md            relatório de qualidade (gerado)
  etica_licenciamento_lgpd.md             ética, licença e LGPD
  guia_databricks.md                      como reproduzir/evidenciar no Databricks
/dados
  bronze/ silver/ gold/                   saídas do pipeline (CSV; no Databricks, Delta Tables)
/evidencias
  (capturas de tela / vídeo da execução no Databricks)
LICENSE
```

## 9. Como reproduzir

```bash
pip install pandas numpy scipy scikit-learn
python scripts/etl_hdi_star_schema.py
python scripts/qualidade_dados.py
python scripts/analise_mobilidade_desigualdade.py
```

Para reproduzir no Databricks (requisito do enunciado), ver `catalogo/guia_databricks.md`.
