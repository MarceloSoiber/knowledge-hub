# 05 — Biblioteca e manutenção de fontes

## Resultado esperado

Consulta, edição e exclusão explícita do acervo já ingerido.

## Escopo

- Listagem de fontes com busca local por título e filtros visuais de metadados.
- Detalhe com conteúdo, origem, tipo, datas e associações.
- Edição de título, conteúdo e metadados suportados pela API.
- Aviso de que alteração de conteúdo provoca novo processamento/embeddings.
- Exclusão com diálogo de confirmação e atualização da listagem após sucesso.

## Endpoints

- `GET /knowledge/sources`
- `GET`, `PATCH`, `DELETE /knowledge/sources/{source_id}`

## Estados e erros

- Fonte não encontrada, conflito de conteúdo duplicado e erro de validação devem fornecer próximo passo claro.
- Enviar `confirm=true` somente após confirmação explícita no diálogo.

## Critérios de aceite

- Uma fonte aberta pela busca exibe seu conteúdo e metadados corretos.
- Edição bem-sucedida reflete imediatamente na tela.
- Exclusão não ocorre por um clique acidental.

## Dependência

Requer fundação. Integra com busca e ingestão por links para a página de detalhe.
