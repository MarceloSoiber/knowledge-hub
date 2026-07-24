# 04 — Ingestão de conhecimento

## Resultado esperado

Inclusão de arquivo ou texto com metadados e retorno claro do processamento.

## Escopo

- Tela com abas “Enviar arquivo” e “Adicionar texto”.
- Arquivo: seleção de arquivo, categorias obrigatórias, tags e projetos opcionais.
- Texto: título, conteúdo e os mesmos metadados.
- Validar campos obrigatórios antes do envio e desabilitar envio duplicado enquanto houver requisição em curso.
- Exibir título, ID da fonte, chunks criados e atalho para a fonte depois do sucesso.

## Endpoints

- `POST /knowledge/uploads`
- `POST /knowledge/texts`
- `GET /knowledge/categories`, `GET /knowledge/tags`, `GET /knowledge/projects`

## Estados e erros

- Informar tipo/tamanho de arquivo não aceito e conteúdo vazio.
- Ao receber duplicidade, exibir link para a fonte existente; não sobrescrever automaticamente.
- Usar indicador indeterminado, pois a API não expõe progresso de embeddings.

## Critérios de aceite

- Um texto válido é ingerido com as categorias escolhidas.
- Um arquivo válido retorna confirmação e permite abrir sua fonte.
- Falhas preservam os campos preenchidos quando for seguro fazê-lo.

## Dependência

Requer fundação e seletor reutilizável de metadados.
