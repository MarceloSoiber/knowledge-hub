# Operacoes do Knowledge Hub

Este runbook cobre reindexacao de embeddings, backup e restauracao. Ele evita
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
