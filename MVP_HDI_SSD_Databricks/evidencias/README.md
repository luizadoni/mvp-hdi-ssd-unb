# Evidências de execução na nuvem (Databricks)

Esta pasta contém as capturas de tela exigidas pelo enunciado, comprovando que o pipeline foi executado e os dados persistidos na plataforma de nuvem (Databricks Free Edition, com Unity Catalog e computação Serverless). Checklist conforme `catalogo/guia_databricks.md`:

- `01_login_databricks.png` — acesso ao workspace Databricks (tela "Welcome to Databricks").
- `02_upload_bronze.png` — upload do arquivo `hdi_full_raw.csv` para o volume Unity Catalog (`/Volumes/workspace/default/hdi_volume/`).
- `03_cluster_ativo.png` — computação ativa (Compute - Serverless: Default Interactive/Automated Compute).
- `04a_celula1_bronze_executada.png` — célula 1 do notebook (ingestão bronze) executada com sucesso.
- `04b_celula2_silver_executada.png` — célula 2 (transformação silver, wide-to-long) executada com sucesso.
- `04c_celula3_gold_executada.png` — célula 3 (modelagem star schema gold) executada com sucesso.
- `04d_celula4_qualidade_executada.png` — célula 4 (indicador de qualidade/completude = 88,29%) executada com sucesso.
- `05_tabelas_delta_persistidas.png` — Catalog mostrando as 6 tabelas Delta persistidas (`hdi_bronze`, `hdi_silver`, `hdi_gold_dim_pais`, `hdi_gold_dim_indicador`, `hdi_gold_dim_ano`, `hdi_gold_fato_indicadores`).
- `06_repositorio_github.png` — repositório público no GitHub com o projeto publicado (evidência complementar de versionamento/entrega).

Cada imagem deve ser referenciada no ponto do README principal (ou do paper) em que sustenta a afirmação correspondente (exigência explícita do enunciado, seção 5.2).
