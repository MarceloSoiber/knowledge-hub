# Quickstart: validar qualidade, segurança e evolução do frontend

## Pré-requisitos

- Node compatível com a versão exigida por Angular CLI (atualmente `>=22.22.3`; Node 24 da imagem Docker é suportado).
- Dependências instaladas em `frontend/` e backend acessível com token de teste, quando o roteiro manual exigir API real.

## Quality gates automatizados

No diretório `frontend/`, execute:

```bash
node --version
npm run typecheck
npm test -- --watch=false
npm run build
```

Qualquer incompatibilidade de Node é bloqueio de qualidade: corrija o ambiente antes de marcar testes/build como aprovados.

## Roteiro manual

1. Em 320 px, 768 px e desktop, navegue por teclado por login, Dashboard, Busca, Pergunte, Ingestão, Biblioteca/detalhe e Organização.
2. Com leitor de tela, confira títulos, labels, loading, erros, vazios e feedback de sucesso; confirme que conteúdo remoto aparece somente como texto.
3. Em uma sessão válida, confira que uma chamada protegida recebe Bearer; force `401` e confirme limpeza da sessão, redirecionamento ao login e ausência do token na tela/mensagem.
4. Exercite ingestão inválida, duplicidade, indisponibilidade, exclusão de fonte/categoria/tag e archive/reactivate; confirme rascunhos, diálogos e retries apropriados.
5. Compare o resultado contra a [matriz de qualidade](contracts/frontend-quality.md) e registre qualquer fluxo não coberto antes da entrega.
