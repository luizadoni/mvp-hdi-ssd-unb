# Como colocar o paper no Overleaf (passo a passo)

O arquivo que você vai usar é `mvp_hdi_short_paper.tex`, nesta mesma pasta. Ele já foi compilado e testado aqui — 7 páginas no total, sendo 6 páginas de texto (Introdução a Conclusão) e as referências bibliográficas terminando numa 7ª página curta (isso é normal e não costuma contar contra o limite de "5 a 6 páginas", que se refere ao corpo do texto).

## 1. Criar conta no Overleaf

1. Acesse https://www.overleaf.com e clique em **Register** (ou já faça login se tiver conta).
2. Pode usar e-mail/senha ou login com Google.

## 2. Criar um novo projeto

1. No painel (dashboard), clique em **New Project** → **Upload Project**.
2. Isso vai pedir um arquivo `.zip`. Como você só tem um `.tex`, use a opção alternativa abaixo (mais simples) ou zipe só o `.tex` antes de subir.

### Alternativa mais simples: Blank Project + colar o conteúdo

1. Clique em **New Project** → **Blank Project**.
2. Dê um nome ao projeto (ex.: "MVP HDI - SSD").
3. O Overleaf abre um editor com um `main.tex` padrão. **Apague todo o conteúdo** desse arquivo.
4. Abra `mvp_hdi_short_paper.tex` no seu computador (num editor de texto simples, ou peça para eu reabrir aqui), copie todo o conteúdo e cole no lugar, substituindo o `main.tex` vazio.
5. Clique em **Recompile** (botão verde no canto superior direito, ou o ícone de "play").

## 3. Ativar hifenização em português (opcional, recomendado)

O arquivo foi compilado aqui sem o pacote `babel` em português porque o ambiente de teste não tinha os dicionários de hifenização instalados. **No Overleaf, esses dicionários já vêm instalados por padrão.** Para ativar a hifenização correta em português (quebra de linha mais bonita, sem "rios" de espaço em branco), adicione esta linha logo depois de `\usepackage[T1]{fontenc}`, no topo do arquivo:

```latex
\usepackage[portuguese]{babel}
```

Depois disso, clique em **Recompile** de novo. Se der algum erro, é só remover essa linha novamente — o documento compila perfeitamente sem ela, só com uma hifenização um pouco menos refinada.

## 4. Revisar o PDF compilado

1. O PDF aparece automaticamente no painel da direita, atualizado a cada "Recompile".
2. Revise especialmente: a Tabela 1 (resumo da auditoria de qualidade), os números citados nos Resultados, e a lista de referências no final.
3. Se quiser trocar seu nome, a data, ou adicionar o link do GitHub do repositório na introdução, edite diretamente no editor do Overleaf — é tempo real, como um Google Docs.

## 5. Baixar o PDF final

1. Clique no ícone de **download** (seta para baixo) no canto superior direito do painel do PDF, ou vá em **Menu** → **Download PDF**.
2. Esse é o arquivo que você entrega na disciplina.

## 6. Problemas comuns

- **"Compilation timed out"**: raro para um documento deste tamanho (7 páginas, sem imagens pesadas); se acontecer, clique em **Recompile** novamente.
- **Erro de pacote não encontrado**: o Overleaf já vem com quase todos os pacotes usados aqui (`babel`, `geometry`, `setspace`, `graphicx`, `hyperref`, `booktabs`, `amsmath`, `caption`, `indentfirst`, `natbib`) pré-instalados; não deve faltar nenhum.
- **Acentos ou caracteres estranhos**: confirme que o arquivo foi salvo em UTF-8 ao copiar e colar (o Overleaf assume UTF-8 por padrão, então isso raramente é um problema).
