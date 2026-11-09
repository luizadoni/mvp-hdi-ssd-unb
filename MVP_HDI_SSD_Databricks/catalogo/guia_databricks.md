# Guia: reproduzindo o pipeline no Databricks (Community Edition, gratuito)

O professor pediu entrega no Databricks. O pipeline deste repositório foi escrito e validado em pandas puro (para você poder testar localmente sem depender de cluster), mas abaixo está o passo a passo para rodá-lo no Databricks e gerar as evidências exigidas (`/evidencias`). Isso é o que fecha os pontos de "Coleta" (0,5) e parte de "Carga" (1,0) na rubrica — persistência efetiva na nuvem, demonstrável.

## Passo 1 — Criar a conta (gratuita)

1. Acesse https://www.databricks.com/try-databricks e escolha **"Get started with Community Edition"** (não a trial de 14 dias paga — a Community Edition é gratuita e permanente, com 1 cluster pequeno).
2. Confirme o e-mail e faça login no workspace (algo como `community.cloud.databricks.com`).
3. **Evidência 1:** print da tela inicial do workspace já logada → salvar em `evidencias/01_login_databricks.png`.

## Passo 2 — Subir o CSV bruto

1. No menu lateral, vá em **Catalog** (ou **Data** em workspaces mais antigos) → **Create Table** / **Upload File**.
2. Faça upload de `dados/bronze/hdi_full_raw.csv` (ou o CSV original `Human Development Index - Full.csv`).
3. Anote o caminho gerado, algo como `/Volumes/workspace/default/hdi_full_raw.csv` (ou `dbfs:/FileStore/tables/hdi_full_raw.csv` em workspaces sem Unity Catalog).
4. **Evidência 2:** print mostrando o arquivo listado no catálogo/volume → `evidencias/02_upload_bronze.png`.

## Passo 3 — Criar o cluster

1. **Compute** → **Create Compute** → escolher o cluster gratuito de single-node (runtime padrão sugerido pela própria tela).
2. Aguardar o status mudar para "Running".
3. **Evidência 3:** print do cluster ativo → `evidencias/03_cluster_ativo.png`.

## Passo 4 — Criar o notebook e colar o ETL adaptado para PySpark

Crie um notebook novo (**Workspace** → **Create** → **Notebook**, linguagem Python) e anexe ao cluster do passo 3. Cole o código abaixo célula a célula — é a tradução direta de `scripts/etl_hdi_star_schema.py` para PySpark (a lógica de negócio é idêntica; só troca pandas por Spark DataFrame API):

```python
# Célula 1 — leitura (bronze)
caminho_bronze = "/Volumes/workspace/default/hdi_full_raw.csv"  # ajuste ao seu caminho real
df_bronze = spark.read.csv(caminho_bronze, header=True, inferSchema=True)
df_bronze.write.format("delta").mode("overwrite").saveAsTable("hdi_bronze")
display(df_bronze.limit(10))
```

```python
# Célula 2 — transformação (silver): wide -> long
import re
from pyspark.sql import functions as F

id_cols = ["ISO3", "Country", "Human Development Groups", "UNDP Developing Regions"]
value_cols = [c for c in df_bronze.columns if c not in id_cols]

# stack dinâmico (equivalente ao pandas.melt)
stack_expr = ", ".join([f"'{c}', `{c}`" for c in value_cols])
df_long = df_bronze.selectExpr(
    *id_cols,
    f"stack({len(value_cols)}, {stack_expr}) as (coluna_origem, valor)"
)

pattern = r"^(.*) \((\d{4})\)$"
df_silver = (
    df_long
    .withColumn("indicador", F.regexp_extract("coluna_origem", pattern, 1))
    .withColumn("ano", F.regexp_extract("coluna_origem", pattern, 2).cast("int"))
    .withColumn("valor", F.col("valor").cast("double"))
    .drop("coluna_origem")
)
df_silver.write.format("delta").mode("overwrite").saveAsTable("hdi_silver")
display(df_silver.limit(10))
```

```python
# Célula 3 — modelagem em estrela (gold)
dim_pais = (
    df_silver.select(
        F.col("ISO3").alias("iso3"), F.col("Country").alias("pais"),
        F.col("Human Development Groups").alias("grupo_hdi"),
        F.col("UNDP Developing Regions").alias("regiao_undp"),
    ).dropDuplicates(["iso3"])
)

dim_indicador = (
    df_silver.select("indicador").distinct()
    .withColumn("indicador_id", F.monotonically_increasing_id())
)

dim_ano = df_silver.select("ano").distinct().orderBy("ano")

fato = (
    df_silver.join(dim_indicador, on="indicador", how="left")
    .select(F.col("ISO3").alias("iso3"), "indicador_id", "ano", "valor")
    .na.drop(subset=["ano"])
)

for nome, tabela in [("dim_pais", dim_pais), ("dim_indicador", dim_indicador),
                      ("dim_ano", dim_ano), ("fato_indicadores", fato)]:
    tabela.write.format("delta").mode("overwrite").saveAsTable(f"hdi_gold_{nome}")

print("Linhas na fato:", fato.count())
```

```python
# Célula 4 — qualidade de dados (completude, como exemplo)
completude = fato.select(
    (F.count(F.when(F.col("valor").isNotNull(), 1)) / F.count("*") * 100).alias("completude_pct")
)
display(completude)
```

5. Execute as 4 células ("Run All").
6. **Evidência 4:** print de cada célula executada com saída visível (sem erro) → `evidencias/04_notebook_executado_databricks.png` (pode ser uma captura por célula ou um vídeo curto rodando tudo).
7. **Evidência 5:** print das tabelas Delta criadas em **Catalog** (`hdi_bronze`, `hdi_silver`, `hdi_gold_*`) → `evidencias/05_tabelas_delta_persistidas.png`. Essa é a evidência mais importante: ela comprova que **os dados estão efetivamente persistidos na nuvem**, exigência explícita da seção 2.3/5.2 do enunciado.

## Passo 5 — Conectar o resultado ao notebook de análise

As perguntas 1, 2 e 3 (classificação ML e mobilidade/desigualdade) podem continuar rodando em Python puro dentro do próprio Databricks (célula `%python` com pandas/scikit-learn — o cluster Community Edition suporta isso normalmente), lendo a tabela gold via:

```python
fato_pd = spark.table("hdi_gold_fato_indicadores").toPandas()
```

Isso evita reescrever o código de ML em PySpark e ainda assim satisfaz o requisito de a análise consumir dado que está persistido na plataforma de nuvem.

## Checklist de evidências mínimas (`/evidencias`)

- [ ] Login/workspace Databricks
- [ ] Upload do CSV bruto
- [ ] Cluster ativo
- [ ] Notebook de ETL executado sem erro (todas as células)
- [ ] Tabelas Delta/gold listadas no Catalog (prova de persistência)
- [ ] Pelo menos 1 resultado de pergunta de negócio (ex.: gráfico de importância de variáveis, ou a tabela de qualidade) rodando a partir do dado lido do Databricks
