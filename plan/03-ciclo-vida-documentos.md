# Plano 03 — Ciclo de vida dos documentos

## Objetivo

Permitir consultar, atualizar e excluir fontes sem depender de nomes ou de limpeza total.

## Escopo

- Adotar UUID público ou ID estável para cada fonte.
- Adicionar hash do conteúdo para detectar duplicatas e alterações.
- Criar `GET /sources/{id}`, `PATCH /sources/{id}` e `DELETE /sources/{id}`.
- Separar alteração de metadados de alteração de conteúdo.
- Recriar embeddings somente quando o conteúdo mudar.
- Definir se exclusão será definitiva ou `soft delete`; para base pessoal, iniciar com
  exclusão definitiva mais confirmação explícita e backup.

## Implementação

1. Remover a identidade implícita baseada em `categoria + título`.
2. Criar serviço transacional para atualização e exclusão.
3. Expor conteúdo original ou armazená-lo separadamente para permitir reprocessamento.
4. Aplicar cascata aos chunks e associações.
5. Criar tools MCP de leitura detalhada; tools destrutivas ficam fora do MCP inicialmente.

## Testes

- Títulos iguais não sobrescrevem documentos diferentes.
- Conteúdo idêntico é detectado conforme a política escolhida.
- Alterar apenas categorias não chama o provider de embeddings.
- Alterar conteúdo substitui os chunks atomicamente.
- Excluir uma fonte remove chunks e associações.

## Critérios de aceite

- Cada documento pode ser administrado individualmente.
- Nenhuma atualização parcial permanece após erro.
- O comportamento de duplicidade está documentado.

