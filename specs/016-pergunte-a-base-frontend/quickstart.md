# Quickstart: Validar Pergunte à Base no Frontend

## Pré-requisitos

- Fundação Angular concluída: autenticação, rota privada, shell, `KnowledgeApiService` e tipos compartilhados.
- API em execução com uma fonte indexada e metadados de teste.
- Token Bearer válido no ambiente local.

## Validar o fluxo principal

1. Inicie API e frontend conforme a documentação do projeto e autentique-se.
2. Abra a rota de perguntas à base.
3. Envie uma pergunta cuja resposta exista em uma fonte indexada.
4. Confirme que a resposta é exibida como texto e que cada fonte mostra título, trecho, localização disponível e metadados.
5. Abra uma fonte e confirme que a rota recebe seu UUID público `source_id`.

## Validar filtros, histórico e cópia

1. Aplique categoria, projeto e uma tag escolhida pelo autocomplete; envie a pergunta e inspecione se a requisição segue [`contracts/frontend-answer.md`](contracts/frontend-answer.md).
2. Remova cada chip e confirme que a pergunta e os outros filtros continuam intactos.
3. Faça duas perguntas bem-sucedidas e confirme que ambas ficam visíveis somente durante a sessão atual.
4. Use “copiar resposta” e “copiar referências”; confirme o conteúdo esperado e o anúncio de sucesso.
5. Recarregue a página ou encerre a sessão; confirme que o histórico desapareceu.

## Validar falhas e acessibilidade

1. Envie texto em branco ou valores fora do intervalo; confirme validação local sem HTTP.
2. Simule `sources: []`, `403`, `422`, `502` e `503`; confirme estado específico, mensagem segura e preservação do formulário.
3. Navegue apenas com Tab, Shift+Tab, Enter e Escape pelos controles, autocomplete, chips, cópia e cartões.
4. Verifique a interface em 320 px e em largura desktop; confira foco visível e anúncios de carregamento/cópia.

## Checks automatizados

```bash
cd frontend
npm run typecheck
npm run build
npm test -- --watch=false
```

Execute a suíte unitária adicionada para o cliente, serialização, estados e cópia antes de concluir a implementação.
