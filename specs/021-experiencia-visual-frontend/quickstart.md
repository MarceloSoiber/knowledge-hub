# Guia de validação: experiência visual e usabilidade

## Pré-requisitos

- Dependências instaladas em `frontend/`.
- API disponível e token válido para exercitar os fluxos autenticados.

## Verificação automatizada

No diretório `frontend/`, executar:

```bash
npm run typecheck
npm test -- --watch=false
npm run build
```

## Roteiro manual

1. Acesse `/inicio` em 1440 px, 768 px e 320 px; confira o [contrato de rotas](contracts/frontend-experience.md) e a página atual destacada.
2. Em mobile, abra o menu, feche com Escape e backdrop e confira a restauração de foco descrita no [modelo local](data-model.md).
3. Use Tab desde o início da página; verifique link de salto, foco visível, navegação, formulários e ações de confirmação.
4. Execute busca e pergunta com filtros; confira que consulta, filtros selecionados, resultados e mensagens tenham hierarquia clara.
5. Faça ingestão de texto e use Biblioteca/Organização; valide estados de carregamento, vazio, erro e sucesso conforme o [contrato de feedback](contracts/frontend-experience.md).
6. Confira que textos longos não gerem rolagem horizontal e que, com redução de movimento do sistema habilitada, animações/transições não sejam necessárias para operar a interface.
