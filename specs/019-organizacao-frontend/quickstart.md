# Quickstart: validar Organização do acervo no frontend

## Pré-requisitos

- Backend com token configurado e ao menos uma fonte usando uma categoria/tag e um projeto.
- Dependências do frontend instaladas em `frontend/`.

## Validação automatizada

No diretório `frontend/`, execute:

```bash
npm run typecheck
npm test -- --watch=false
npm run build
```

## Fluxo manual

1. Autentique-se e abra `/organizacao`; confirme estados de carregamento, vazio, erro/retry e as três áreas de manutenção.
2. Crie e renomeie categoria/tag; confirme atualização imediata em um seletor de outra rota sem recarga completa.
3. Tente excluir uma categoria/tag vinculada a fonte e confirme diálogo, resposta de conflito e preservação do item. Exclua um item não usado após confirmar.
4. Em Ingestão e no detalhe de fonte, digite em tags e confirme sugestões, teclado, seleção múltipla e ausência de duplicatas.
5. Crie e edite projeto, arquive-o e confirme que não é opção ativa; filtre arquivados, reative-o e confirme seu retorno.
6. Abra fontes de um projeto, valide estado vazio quando aplicável e navegue a uma fonte por seu UUID.
7. Repita os fluxos por teclado em 320 px, 768 px e desktop; verifique foco, diálogos e anúncios de status.
