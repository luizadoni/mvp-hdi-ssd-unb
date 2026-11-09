# Como publicar este repositório no GitHub (passo a passo)

1. Crie uma conta gratuita em https://github.com, se ainda não tiver.
2. Clique em **New repository** (botão verde, ou "+" no canto superior direito → "New repository").
3. Nome sugerido: `mvp-hdi-ssd-unb`. Marque **Public** (obrigatório pelo enunciado). Não marque "Add a README" (você já tem um).
4. Clique em **Create repository**.
5. No seu computador, abra o terminal na pasta deste projeto (a pasta que contém este `GUIA_PUBLICACAO_GITHUB.md`) e rode:

```bash
git init
git add .
git commit -m "MVP HDI - pipeline completo (busca, coleta, modelagem, carga, análise)"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/mvp-hdi-ssd-unb.git
git push -u origin main
```

(Substitua `SEU_USUARIO` pelo seu usuário do GitHub. Se nunca usou git pelo terminal, o próprio GitHub mostra esse mesmo bloco de comandos na tela logo após criar o repositório — pode copiar de lá.)

6. Confirme que o repositório está público: abra o link em uma janela anônima do navegador (sem estar logado). Se conseguir ver os arquivos, está correto — esse é o mesmo teste que o enunciado pede no checklist de entrega (item 9).
7. Copie o link do repositório (ex.: `https://github.com/SEU_USUARIO/mvp-hdi-ssd-unb`) e cole no fórum de entrega da disciplina, conforme pedido na seção 5.3 do enunciado.

## Se preferir não usar o terminal

No GitHub, após criar o repositório vazio, use o botão **"uploading an existing file"** na própria página do repositório e arraste a pasta/arquivos (o GitHub aceita arrastar múltiplos arquivos de uma vez, mas não pastas inteiras pelo navegador em todos os casos — para subir a estrutura de pastas completa, o caminho pelo terminal acima é mais confiável).
