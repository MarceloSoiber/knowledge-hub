# 03 — Pergunte à base

## Resultado esperado

Uma pessoa faz uma pergunta em linguagem natural, lê a resposta e verifica as fontes que a sustentam.

## Escopo

- Formulário de pergunta com filtros de categoria, tag, projeto, limite e score mínimo.
- Exibir resposta, carregamento e fontes retornadas como cartões clicáveis.
- Permitir copiar a resposta e as referências apresentadas.
- Manter histórico apenas em memória da sessão; não persistir conversas nesta fase.

## Endpoint

- `POST /knowledge/answer`

## Estados e erros

- Distinguir resposta sem fontes, falha de embeddings/LLM, API indisponível e bloqueio por conteúdo sensível.
- Renderizar resposta e trechos como texto confiável apenas para exibição; nunca interpretar HTML vindo da base.

## Critérios de aceite

- Cada fonte retornada pode ser aberta no detalhe da biblioteca.
- A pergunta e os filtros permanecem visíveis após uma falha para permitir nova tentativa.
- O histórico desaparece ao encerrar ou renovar a sessão.

## Dependência

Requer fundação e componentes de filtros; pode ser desenvolvida em paralelo à busca após a Fase 01.
