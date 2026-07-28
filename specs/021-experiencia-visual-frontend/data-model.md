# Modelo de design local

Não há modelo persistido, migração ou alteração de API. Este documento descreve apenas o estado e os contratos de apresentação no cliente.

## Design tokens

| Grupo | Exemplos | Regra |
| --- | --- | --- |
| Cor | texto, superfície, borda, primária, sucesso, alerta, perigo, foco | Cada valor tem significado semântico; componentes não repetem hexadecimais sem necessidade. |
| Espaço e tamanho | escala de espaçamento, largura de conteúdo, altura mínima de controle | Garante alinhamento, área de toque e responsividade. |
| Tipografia | famílias, tamanhos, pesos, alturas de linha | Separa título, corpo, texto auxiliar e rótulo. |
| Forma e elevação | raios, bordas, sombras | Distingue agrupamentos e superfícies sem excesso de ornamento. |
| Movimento | duração e transição | Transições são discretas e desativadas/reduzidas por preferência do usuário. |

## Padrões de apresentação

| Padrão | Variantes | Regras de uso |
| --- | --- | --- |
| Botão/ação | primária, secundária, perigo, texto | Apenas uma ação primária por bloco de tarefa; ações destrutivas usam rótulo explícito e confirmação existente. |
| Cabeçalho de página | etiqueta, título, descrição, ação contextual opcional | Um único `h1`, descrição curta e relação visível com a navegação. |
| Cartão/painel | conteúdo, resultado, métrica, formulário | Agrupa informação relacionada, preserva título semântico e não vira contêiner genérico para toda a página. |
| Campo e filtros | entrada principal, controles avançados, chips | Rótulos persistentes, erro associado e seleção removível por teclado. |
| Feedback | carregando, vazio, sucesso, erro, validação | Texto orienta a ação e não depende só de cor; erro recuperável inclui retry próximo. |

## Estado de navegação móvel

| Estado | Entrada | Saída esperada |
| --- | --- | --- |
| Fechado | rota inicial, clique em link, Escape, backdrop | Sidebar oculta e botão de menu focável. |
| Aberto | botão do menu | Navegação visível, backdrop disponível e `aria-expanded=true`. |
| Fechando | link, backdrop ou Escape | Sidebar oculta; Escape/backdrop devolve foco ao botão, enquanto um link transfere foco pelo fluxo normal da rota. |

## Preferência de tema

| Campo | Valores | Regra |
| --- | --- | --- |
| Tema atual | `light`, `dark` | Aplicado como `data-theme` no elemento raiz e refletido em `color-scheme`. |
| Persistência | `localStorage: knowledge-hub.theme` | Uma escolha explícita substitui a preferência do sistema somente neste navegador. |
| Padrão inicial | tema do sistema | Usado quando não há valor local válido. |
