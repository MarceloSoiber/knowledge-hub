# Contrato de experiência do frontend

## Rotas privadas preservadas

| Rota | Rótulo de navegação | Objetivo |
| --- | --- | --- |
| `/inicio` | Início | Resumo e próximos passos do acervo. |
| `/busca` | Busca inteligente | Encontrar conteúdo e fontes. |
| `/perguntar` | Pergunte à base | Obter resposta auditável. |
| `/ingestao` | Ingestão | Adicionar arquivo ou texto. |
| `/biblioteca` | Biblioteca | Consultar e filtrar fontes. |
| `/organizacao` | Organização | Manter categorias, tags e projetos. |

As rotas, seus guards e seus contratos HTTP não mudam.

## Contrato de interação

- O shell contém um link de salto para `#main-content`, navegação com nome acessível e o conteúdo principal em `<main>`.
- O item da rota ativa possui um sinal visual e semântico (`aria-current="page"` quando aplicável).
- O botão do menu móvel expõe estado com `aria-expanded` e controla a navegação nomeada por `aria-controls`.
- Escape e backdrop fecham a gaveta; o foco retorna ao botão quando a interação que fechou foi Escape ou backdrop.
- O botão de tema informa a ação seguinte (usar tema claro/escuro), expõe seu estado por `aria-pressed` e não depende de cor ou do ícone para ser compreendido.
- Em desktop, a navegação compacta exibe ícones SVG acompanhados por tooltip em mouse e foco; cada link conserva nome acessível. Em mobile, a gaveta expõe ícone e texto.
- Controles ativáveis por teclado usam elementos nativos (`a`, `button`, `input`, `select`, `textarea`) e foco visível global.
- Conteúdo remoto é sempre interpolado como texto, nunca transformado em HTML.

## Contrato de feedback

| Situação | Apresentação | Ação |
| --- | --- | --- |
| Carregamento | texto de progresso e indicador não essencial | A rota continua navegável. |
| Vazio | descrição que diferencia ausência de dados de erro | Oferece ação de criação/limpeza quando houver uma próxima etapa. |
| Erro recuperável | mensagem curta e contextual, anunciada adequadamente | Retry local; não descarta dados válidos. |
| Sucesso | confirmação junto da tarefa concluída | Link para continuar, quando relevante. |
| Ação destrutiva | estilo de perigo e diálogo de confirmação atual | Executa somente após confirmação explícita. |
