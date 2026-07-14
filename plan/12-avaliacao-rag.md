# Plano 12 — Avaliação do RAG

## Objetivo

Medir a qualidade da recuperação e impedir regressões ao mudar chunking, embeddings ou busca.

## Dataset

Criar casos versionados sem dados pessoais sensíveis, contendo:

- pergunta;
- fontes e chunks esperados;
- categoria/projeto esperado;
- resposta esperada ou pontos essenciais;
- perguntas deliberadamente sem resposta;
- casos com termos exatos e casos semânticos.

## Métricas

- Recall@K e Mean Reciprocal Rank para recuperação.
- Taxa de resposta correta para perguntas conhecidas.
- Taxa de recusa correta quando não há contexto.
- Citações corretas e sustentação da resposta pelas fontes.
- Latência de embeddings, busca e resposta.

## Implementação

1. Criar runner separado dos testes unitários.
2. Fixar versão do dataset e configuração avaliada.
3. Produzir relatório comparando baseline e candidato.
4. Definir limites mínimos para aprovar mudanças de recuperação.

## Critérios de aceite

- Existe baseline reproduzível da implementação atual.
- Busca híbrida, threshold e novos modelos só entram após comparação objetiva.
- Perguntas sem resposta fazem parte obrigatória do conjunto.

