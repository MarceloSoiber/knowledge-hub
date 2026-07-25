# Quickstart: Validar Busca Inteligente no Frontend

## Pré-requisitos

- Fase 01 da fundação concluída: autenticação, rota privada, `KnowledgeApiService`, tipos e componentes compartilhados.
- API em execução com uma fonte indexada e categorias/tags/projetos de teste.
- Um token Bearer válido para o ambiente local.

## Validar o fluxo principal

1. Inicie a API e o frontend conforme os comandos documentados do projeto.
2. Autentique-se e abra a rota de busca.
3. Pesquise um termo conhecido de uma fonte indexada.
4. Confirme que cada resultado mostra título, trecho, localização disponível, chips e score quando ele existir.
5. Abra o link de uma fonte e confirme que a rota recebe o UUID público da fonte.

## Validar filtros e diagnóstico

1. Selecione uma categoria e um projeto, escolha uma tag pelas sugestões e execute a busca.
2. Inspecione a requisição: ela deve seguir [`contracts/frontend-search.md`](contracts/frontend-search.md) e enviar os IDs corretos.
3. Remova cada chip individualmente e confirme que o texto da consulta não mudou.
4. Ative os motivos de correspondência, pesquise novamente e confirme a exibição de `vector`/`text` somente quando a API responder com eles.

## Validar falhas e acessibilidade

1. Pesquise texto em branco; confirme validação local sem chamada HTTP.
2. Simule resposta vazia, `422`, `404`, `502` e `503`; confirme mensagem acionável, sem token ou corpo de erro cru, e preservação do formulário.
3. Use apenas Tab, Shift+Tab, Enter e Escape para operar formulário, autocomplete, chips e links.
4. Verifique em viewport de 320 px e em largura desktop.

## Checks automatizados

```bash
cd frontend
npm run typecheck
npm run build
```

Execute também a suíte unitária configurada pela fundação para o cliente HTTP e a feature de busca.
