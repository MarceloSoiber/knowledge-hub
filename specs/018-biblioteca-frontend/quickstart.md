# Quickstart: validar Biblioteca e manutenção de fontes

## Pré-requisitos

- Backend acessível com ao menos duas fontes autenticadamente visíveis, de associações diferentes.
- Frontend configurado e dependências instaladas em `frontend/`.

## Validação automatizada

No diretório `frontend/`, execute:

```bash
npm run typecheck
npm test -- --watch=false
npm run build
```

Os testes devem cobrir serialização de PATCH/DELETE, filtragem local, atualização de estado, diálogos e os erros do [contrato de frontend](contracts/frontend-library.md).

## Fluxo manual

1. Autentique-se e abra `/biblioteca`; confirme a listagem ou o estado vazio/erro adequado.
2. Pesquise por parte de um título e aplique categorias, tags e projetos; confirme que a lista muda sem nova requisição `GET /sources`.
3. Abra uma fonte e confirme conteúdo, URI, tipo, hash, datas e associações.
4. Edite título e uma associação; salve e confirme a atualização imediata. Depois altere conteúdo e confirme a exibição do aviso de reprocessamento antes de salvar.
5. Simule/valide conflitos e erros conforme [o contrato](contracts/frontend-library.md); confirme preservação do rascunho e mensagem acionável.
6. Abra exclusão, cancele usando o botão e Escape, e confirme que não há DELETE. Reabra, confirme, verifique `confirm=true`, retorno à Biblioteca e ausência da fonte.
7. Repita os fluxos por teclado em 320 px, 768 px e desktop; confirme foco visível, diálogo acessível e anúncios de estados.
