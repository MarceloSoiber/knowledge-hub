# Quickstart: Validar Ingestão no Frontend

## Pré-requisitos

- Backend e PostgreSQL disponíveis com ao menos uma categoria, e token configurado quando a autenticação estiver ativa.
- Dependências instaladas em `frontend/`.
- Uma fonte de teste `.txt`, `.md` ou `.pdf` de no máximo 10 MB, com conteúdo que ainda não exista na base.

## Verificações automatizadas

No diretório `frontend/`, executar:

```bash
npm run typecheck
npm test -- --watch=false
npm run build
```

Os testes devem cobrir os contratos em [`contracts/frontend-ingestion.md`](contracts/frontend-ingestion.md) e os estados definidos em [`data-model.md`](data-model.md).

## Cenário manual: arquivo

1. Autenticar e abrir `/ingestao`.
2. Na aba **Enviar arquivo**, escolher um arquivo permitido e ao menos uma categoria; adicionar tag/projeto opcional.
3. Enviar e confirmar indicador indeterminado com controles de reenvio desabilitados.
4. Confirmar título, UUID público, quantidade de chunks e o link que abre a fonte criada.
5. Tentar arquivo de extensão inválida e arquivo maior que 10 MB; confirmar que não há requisição e a mensagem é associada ao campo.

## Cenário manual: texto

1. Na aba **Adicionar texto**, preencher título, conteúdo e categoria.
2. Enviar e confirmar a mesma confirmação de fonte.
3. Testar título/espaços, conteúdo somente com espaços e nenhuma categoria; confirmar validação sem chamada HTTP.
4. Simular ou usar conteúdo duplicado; confirmar mensagem de duplicidade e link à fonte existente, sem sobrescrita.

## Acessibilidade e recuperação

1. Em 320 px, operar abas, seleção múltipla, campos, envio, link de resultado e recarregamento de metadados somente por teclado.
2. Confirmar foco visível e anúncios de processamento, erro e sucesso.
3. Simular `404`, `413`, `502` e `503`; confirmar mensagem segura, ação aplicável e preservação dos dados do formulário quando segura.
