# Roadmap do Knowledge Hub

Planos incrementais para transformar o projeto em uma base pessoal de conhecimento
consultável por agentes de IA. Execute um plano por vez e só avance quando seus critérios
de aceite estiverem atendidos.

## Ordem de execução

| Ordem | Plano | Resultado esperado | Depende de |
| --- | --- | --- | --- |
| 01 | [Categorias muitos-para-muitos](01-categorias-muitos-para-muitos.md) | Um documento pode ter várias categorias e elas podem ser administradas. | Estado atual |
| 02 | [Ingestão de texto pelo MCP](02-ingestao-texto-mcp.md) | Agentes autorizados podem salvar conhecimento textual. | 01 |
| 03 | [Ciclo de vida dos documentos](03-ciclo-vida-documentos.md) | Consultar, editar e excluir conhecimento individualmente. | 01 |
| 04 | [Metadados e citações na busca](04-metadados-citacoes.md) | Resultados rastreáveis, com origem e localização. | 01 e 03 |
| 05 | [Limite mínimo de relevância](05-limite-relevancia.md) | Evitar contexto irrelevante e falsas respostas. | 04 |
| 06 | [Busca híbrida](06-busca-hibrida.md) | Combinar semântica com termos exatos. | 04 e 05 |
| 07 | [Tags](07-tags.md) | Classificação livre complementar às categorias. | 01 |
| 08 | [Projetos](08-projetos.md) | Associar conhecimento a projetos sem duplicá-lo. | 01 e 03 |
| 09 | [Versionamento de embeddings](09-versionamento-embeddings.md) | Saber como cada vetor foi produzido. | 03 |
| 10 | [Reindexação e backup](10-reindexacao-backup.md) | Recuperar dados e trocar embeddings com segurança. | 09 |
| 11 | [Índice vetorial HNSW](11-indice-hnsw.md) | Busca vetorial escalável. | 09 e 10 |
| 12 | [Avaliação do RAG](12-avaliacao-rag.md) | Medir recuperação e qualidade antes de mudanças. | 05 e 06 |
| 13 | [Integração com agentes](13-integracao-agentes.md) | Fazer a IA consultar a base no momento correto. | 02, 04, 05 e 12 |

## Regra de execução

Para cada plano:

1. Criar uma branch ou commit de referência.
2. Confirmar o backup quando houver migração destrutiva.
3. Implementar somente o escopo descrito.
4. Executar testes automatizados e validação manual.
5. Atualizar `doc/API.md` e o README quando o contrato mudar.
6. Registrar decisões que divergirem do plano.
7. Só iniciar o próximo plano após atender todos os critérios de aceite.

## Princípios do roadmap

- Nenhuma gravação feita por agente deve ser silenciosa.
- Conhecimento sensível não deve sair do ambiente local sem decisão explícita.
- Todo resultado recuperado deve ser rastreável até sua origem.
- Migrações devem preservar os dados existentes.
- Categorias são assuntos controlados; tipo da fonte, projeto e tags são dimensões distintas.
- Mudanças no modelo de embeddings exigem reindexação, não mistura de vetores incompatíveis.

