# Plano 05 — Limite mínimo de relevância

## Objetivo

Evitar que resultados semanticamente fracos sejam apresentados como conhecimento válido.

## Implementação

1. Criar configuração `SEARCH_MIN_SCORE` com valor inicial conservador.
2. Aplicar o limite após calcular a similaridade cosseno.
3. Permitir ajuste controlado por endpoint/tool, dentro de limites seguros, ou manter apenas
   configuração global durante a calibração.
4. Quando nenhum resultado passar, retornar lista vazia e instruir o LLM a declarar ausência.
5. Registrar scores para análise sem armazenar perguntas sensíveis em logs por padrão.

## Calibração

- Montar perguntas relevantes e irrelevantes para cada domínio.
- Medir falsos positivos e falsos negativos.
- Não assumir que `1 - distância` é uma probabilidade.
- Calibrar novamente ao trocar o modelo de embeddings.

## Testes

- Resultados abaixo do limite são removidos.
- Nenhum resultado gera resposta explícita de informação não encontrada.
- Limites inválidos são rejeitados.

## Critérios de aceite

- Perguntas fora da base não recebem chunks aleatórios.
- O valor padrão e sua justificativa estão documentados.

