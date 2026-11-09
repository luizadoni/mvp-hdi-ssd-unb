# Ética, licenciamento e proteção de dados

Seção exigida pelo enunciado (item 4) — registrada separadamente do README para facilitar a localização pelo avaliador.

## 1. Licença da base de dados

- **Fonte:** UNDP Human Development Report Office — https://hdr.undp.org/data-center
- **Natureza:** dados estatísticos públicos, agregados por país (não há registro individual de pessoa).
- **Licença:** o PNUD disponibiliza os dados dos relatórios de Desenvolvimento Humano para uso livre, incluindo fins acadêmicos e de pesquisa, com exigência de citação da fonte. Não há cláusula que impeça redistribuição de recortes do conjunto de dados.
- **Decisão tomada:** como a licença permite republicação, o CSV bruto foi versionado em `dados/bronze/` neste repositório (se a licença não permitisse, apenas o script de coleta seria publicado, nunca os dados brutos — regra geral seguida neste projeto).

## 2. Dados pessoais (LGPD — Lei nº 13.709/2018)

- A base é **100% agregada por país** (ex.: expectativa de vida média do país, não de indivíduos). Não há nome, CPF, e-mail, localização individual ou qualquer identificador de pessoa física.
- Não há, portanto, incidência de dado pessoal na acepção do art. 5º da LGPD, e nenhuma anonimização adicional foi necessária.
- Caso o projeto venha a ser estendido com dados em grão individual (ex.: microdados de pesquisas domiciliares), a recomendação registrada para trabalhos futuros é: (a) preferir bases já anonimizadas/agregadas publicadas por institutos oficiais; (b) se houver identificador direto, aplicar pseudonimização antes de qualquer carga, documentando o procedimento nesta mesma seção.

## 3. Dados corporativos

Não se aplica — o projeto não utiliza dados de empresa, cliente ou terceiro privado. Toda a base é de fonte pública multilateral (PNUD/ONU).

## 4. Coleta automatizada (web scraping)

Não foi necessário nenhum robô de coleta: o conjunto de dados foi obtido como arquivo CSV único, publicado oficialmente pelo PNUD (replicado via Kaggle). Não há, portanto, questão de termos de uso de scraping a observar nesta entrega.

## 5. Resumo para o checklist de entrega

| Item do checklist | Status |
|---|---|
| Licença do conjunto de dados registrada | Sim — PNUD, uso livre com citação |
| Dado pessoal identificado e tratado (LGPD) | Não aplicável — base agregada por país |
| Autorização para uso de dado corporativo | Não aplicável — base pública |
| Ética de coleta (scraping) observada | Não aplicável — download direto, sem scraping |
