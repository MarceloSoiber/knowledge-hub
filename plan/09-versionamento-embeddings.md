# Plano 09 — Versionamento de embeddings

## Objetivo

Impedir a mistura silenciosa de vetores produzidos por modelos ou configurações diferentes.

## Modelo proposto

Registrar por chunk ou por lote de indexação:

- `embedding_provider`;
- `embedding_model`;
- `embedding_dimension`;
- `embedding_version` ou revisão;
- `embedded_at`;
- hash do conteúdo normalizado.

## Implementação

1. Criar entidade/lote de indexação para evitar repetir metadados em todos os chunks, se útil.
2. Persistir a configuração efetiva durante ingestão.
3. Validar compatibilidade antes da busca.
4. Marcar chunks antigos como pendentes quando a configuração mudar.
5. Impedir inicialização com dimensão divergente da coluna sem uma migração explícita.

## Testes

- Ingestão registra modelo e dimensão corretos.
- Busca não mistura versões incompatíveis.
- Mudança de modelo identifica conteúdo pendente de reindexação.
- Hash igual evita trabalho desnecessário.

## Critérios de aceite

- É possível responder exatamente qual modelo produziu qualquer embedding.
- Trocar configuração não degrada a base silenciosamente.

