# Operacoes do Knowledge Hub

Este runbook cobre reindexacao de embeddings, indice HNSW, backup e restauracao. Ele evita
imprimir tokens, URLs com senha e conteudo integral das fontes nos logs.

## Reindexacao de embeddings

Use dry-run antes de executar:

```bash
reindex-embeddings --dry-run --batch-size 50
```

Filtros disponiveis:

```bash
reindex-embeddings --dry-run --source-id "$SOURCE_PUBLIC_ID"
reindex-embeddings --dry-run --category "docs"
```

Executar uma fatia limitada:

```bash
reindex-embeddings --batch-size 50
```

Retomar um run:

```bash
reindex-embeddings --resume-run-id "$RUN_ID" --batch-size 50
```

O comando persiste `ReindexRun` e `ReindexItem`, reavalia compatibilidade antes
de chamar o provider e atualiza apenas chunks que continuam pendentes,
incompativeis ou falhos. A saida usa ids, contadores e erros sanitizados.

Limite atual: o modelo de dados possui uma coluna `knowledge_chunks.embedding`.
Assim, a reindexacao atualiza o vetor do chunk existente depois de obter um vetor
compativel. Uma troca blue/green mantendo vetores antigos e novos em paralelo
exige uma tabela adicional de vetores por chunk.

## Backup

Use formato custom do PostgreSQL e armazene o arquivo fora do volume principal:

```bash
pg_dump --format=custom --no-owner --file "$BACKUP_PATH" "$DATABASE_URL"
sha256sum "$BACKUP_PATH" > "$BACKUP_PATH.sha256"
```

Criptografe antes de enviar para destino externo quando o destino nao fornecer
criptografia equivalente:

```bash
gpg --symmetric --cipher-algo AES256 "$BACKUP_PATH"
```

O helper abaixo imprime comandos com URL redigida:

```bash
knowledge-backup --backup-path "$BACKUP_PATH" --restore-database "$RESTORE_DATABASE"
```

### Incluir ou regenerar embeddings

Incluir embeddings no dump preserva buscas vetoriais imediatamente apos restore,
mas aumenta o artefato. Regenerar embeddings reduz tamanho quando o custo de
reindexacao for aceitavel; nesse caso, documente a decisao e execute:

```bash
reindex-embeddings --dry-run
reindex-embeddings --batch-size 50
```

## Restauracao

Restaure sempre primeiro em um banco vazio:

```bash
createdb "$RESTORE_DATABASE"
psql "$RESTORE_DATABASE" -c "CREATE EXTENSION IF NOT EXISTS vector;"
pg_restore --no-owner --dbname "$RESTORE_DATABASE" "$BACKUP_PATH"
```

Checklist minimo:

- Extensao pgvector habilitada.
- Contagem de fontes igual ao ambiente original.
- Contagem de chunks coerente com a estrategia escolhida.
- Relacoes de categorias, tags e projetos preservadas.
- Uma busca de amostra retorna conteudo esperado.
- Se embeddings foram omitidos ou invalidados, `reindex-embeddings --dry-run`
  mostra candidatos esperados.

## Retencao e destino

Defina antes de agendar:

- Janela de retencao em dias.
- Destino fora do volume principal do banco.
- Criptografia do artefato ou do destino.
- Processo de verificacao de checksum.
- Responsavel por executar restore de validacao periodico.

## Agendamento

Agendamento fica bloqueado ate existir um teste real de restauracao documentado
com data, artefato, banco vazio de destino, contagens e busca de amostra.

Exemplo de comando para timer/cron depois da validacao:

```bash
pg_dump --format=custom --no-owner --file "$BACKUP_PATH" "$DATABASE_URL"
sha256sum "$BACKUP_PATH" > "$BACKUP_PATH.sha256"
gpg --symmetric --cipher-algo AES256 "$BACKUP_PATH"
```

Nao grave `DATABASE_URL` com senha em logs de agendamento. Prefira `.pgpass`,
service files do PostgreSQL ou variaveis de ambiente protegidas.

## Indice vetorial HNSW

O indice `ix_knowledge_chunks_embedding_hnsw_cosine` acelera a ordenacao por
distancia de cosseno dos chunks com embeddings compativeis com a configuracao
ativa. Ele nao muda endpoints HTTP, tools MCP ou o formato das respostas de
busca. A operacao exige pgvector 0.5 ou superior, corpus representativo ja
embutido e consultas de avaliacao com pelo menos um caso sem filtro, por
categoria e por projeto.

Copie `evaluation/hnsw-queries.example.json` para um arquivo local e ajuste os
identificadores de categoria e projeto para o ambiente. Primeiro capture a
linha de base exata:

```bash
knowledge-hnsw baseline \
  --queries evaluation/hnsw-queries.json \
  --limit 10 \
  --output reports/hnsw-baseline.json
```

O baseline desabilita scans de indice apenas na sessao de medicao. O relatorio
registra os IDs de top-k, p50/p95, plano JSON com buffers e filtros aplicados.
Ele nao cria nem remove objetos de schema.

Crie o indice somente depois de revisar o baseline. Por padrao, o comando exige
10.000 chunks compativeis; ajuste esse limite com evidencia ou use `--force`
para uma avaliacao controlada em corpus menor.

```bash
knowledge-hnsw create --min-chunks 10000 --output reports/hnsw-create.json
```

O comando usa `CREATE INDEX IF NOT EXISTS ... USING hnsw (embedding
vector_cosine_ops)` e executa `ANALYZE knowledge_chunks`. Para tabelas grandes,
execute a variante `CREATE INDEX CONCURRENTLY` fora de qualquer transacao usando
o SQL exibido pelo modulo operacional; nao inclua essa operacao no startup da
aplicacao.

Valide recall e latencia com o mesmo conjunto de consultas:

```bash
knowledge-hnsw validate \
  --queries evaluation/hnsw-queries.json \
  --baseline reports/hnsw-baseline.json \
  --recall-threshold 0.95 \
  --hnsw-ef-search 80 \
  --output reports/hnsw-validation.json
```

Aceite o indice apenas quando recall@k atender ao limiar acordado, p95 melhorar
e os resultados filtrados permanecerem corretos. O campo `decision` do
relatorio registra `accepted`, `rejected` ou `inconclusive`; planos que nao
selecionam o indice para filtros seletivos sao uma ressalva medida, nao motivo
para mudar o contrato de busca.

HNSW ocupa memoria adicional durante a construcao, amplia o armazenamento do
banco e torna insercoes/reindexacoes mais lentas. Antes da promocao, execute
uma reindexacao em volume representativo e registre duracao, contagem de
chunks, tamanho do indice e p95 de busca no relatorio de mudanca:

```bash
reindex-embeddings --dry-run --batch-size 50
reindex-embeddings --batch-size 50
```

O rollback e explicito. Sem `--execute`, o comando apenas exibe o SQL; com a
flag ele remove o indice em uma transacao controlada. Em producao, prefira
`DROP INDEX CONCURRENTLY IF EXISTS ix_knowledge_chunks_embedding_hnsw_cosine`
fora de uma transacao.

```bash
knowledge-hnsw drop
knowledge-hnsw drop --execute
```
