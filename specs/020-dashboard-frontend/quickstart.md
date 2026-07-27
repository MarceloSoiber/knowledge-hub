# Quickstart: validar Dashboard inicial do acervo

## Pré-requisitos

- Frontend configurado e dependências instaladas em `frontend/`.
- Backend acessível com token válido; para a validação completa, preparar fontes com datas distintas e projetos ativos e arquivados.

## Validação automatizada

No diretório `frontend/`, execute:

```bash
npm run typecheck
npm test -- --watch=false
npm run build
```

Os testes devem cobrir os contratos em [frontend-dashboard.md](contracts/frontend-dashboard.md), as métricas, a ordenação e os estados independentes.

## Fluxo manual

1. Autentique-se e abra `/inicio`; confirme que os cinco cartões correspondem às coleções devolvidas pela API.
2. Verifique que até cinco fontes aparecem da mais nova para a mais antiga e que cada uma abre `/sources/:sourceId`.
3. Simule atraso ou falha em uma coleção secundária; confirme que atalhos e demais áreas continuam utilizáveis e que o retry é localizado.
4. Use os atalhos Busca, Pergunte à base e Ingestão por teclado e mouse; confira as rotas corretas.
5. Retorne listas vazias; confirme zeros legíveis, ausência de recentes quebrados e chamada para a primeira ingestão.
6. Repita em 320 px, 768 px e desktop, verificando landmarks, foco, links, contraste e anúncios de estado.
