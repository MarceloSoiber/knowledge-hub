# Plano 02 — Ingestão de texto pelo MCP

## Objetivo

Criar uma tool `ingest_text` para agentes salvarem notas e conhecimento sem arquivo.

## Escopo

- Entrada: `title`, `content`, `category_ids` e metadados opcionais permitidos.
- Reutilizar o serviço de ingestão usado pela API, sem duplicar regras.
- Retornar `source_id`, título, categorias e quantidade de chunks.
- Separar autorização de leitura (`knowledge:read`) e escrita (`knowledge:write`).
- Exigir confirmação do usuário nas instruções da tool antes de persistir conteúdo.

## Implementação

1. Criar modelos Pydantic específicos para entrada e saída MCP.
2. Adicionar a função em `mcp_server/tools/knowledge.py` e registrá-la no servidor.
3. Validar como a versão do FastMCP aplica escopo por tool; se não houver suporte seguro,
   separar escrita em outro servidor ou manter a tool desabilitada por configuração.
4. Converter erros de categoria, embeddings e validação em mensagens úteis.
5. Registrar origem como `mcp` e, quando possível, o cliente responsável.

## Testes

- Ingestão válida cria fonte e chunks.
- Categoria inexistente e conteúdo vazio falham sem gravar dados.
- Falha no embedding provoca rollback.
- Cliente somente leitura não consegue executar a tool.
- Recadastro segue a política de identidade definida no Plano 03.

## Critérios de aceite

- A tool aparece no catálogo MCP com descrição clara.
- Escrita não é possível com credenciais somente de leitura.
- A IA não é instruída a salvar conversas automaticamente.

