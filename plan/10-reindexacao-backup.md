# Plano 10 — Reindexação e backup

## Objetivo

Permitir trocar embeddings e recuperar a base sem perder conhecimento pessoal.

## Reindexação

1. Criar comando CLI com `--dry-run`, seleção por fonte/categoria e tamanho de lote.
2. Reprocessar a partir do conteúdo original preservado no Plano 03.
3. Tornar a operação retomável, registrando progresso e erro por fonte.
4. Criar novos vetores antes de remover os antigos quando houver espaço.
5. Validar contagens, dimensões e amostras antes de ativar a nova versão.

## Backup

1. Criar comandos documentados para `pg_dump` e restauração.
2. Incluir tabelas, configuração e conteúdo original; embeddings podem ser incluídos ou
   regenerados conforme custo e tamanho.
3. Definir retenção, criptografia e destino fora do volume principal.
4. Automatizar backup agendado somente após testar restauração.
5. Nunca imprimir tokens ou conteúdo sensível nos logs.

## Testes

- Interrupção e retomada não duplicam chunks.
- Falha em uma fonte não corrompe as demais.
- Restauração em banco vazio reproduz fontes, relações e buscas.

## Critérios de aceite

- Um teste real de restauração foi executado e documentado.
- Reindexação pode ser pausada e retomada com segurança.

