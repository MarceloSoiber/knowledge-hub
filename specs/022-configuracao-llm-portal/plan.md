# Implementation Plan: Configuração de IA pelo portal

**Branch**: `022-configuracao-llm-portal` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)

**Input**: Tornar ajustáveis no portal o provedor, URLs, modelos, chave API, embeddings e dimensão vetorial mostrados no ambiente, e concentrar tema, Configurações e desconexão em um menu de usuário.

## Summary

Criar uma área privada de Configurações de IA para administrar `LLM_PROVIDER`, endpoints e modelos locais/API, `API_KEY`, `EMBEDDING_MODEL` e `VECTOR_DIM`. A persistência reutiliza `app_config`, tabela chave-valor já criada e usada pelo projeto, em vez de introduzir uma tabela duplicada. O ambiente continua como fallback de boot; no Docker Compose, `DOCKER_LOCAL_LLM_BASE_URL` alimenta `LOCAL_LLM_BASE_URL`. Em runtime, valores salvos no portal têm precedência e são resolvidos a cada nova dependência de cliente. A chave API será cifrada no banco e nunca retornará ao navegador. Alterações de provedor/modelo de embeddings exigem reindexação; `VECTOR_DIM` recebe um fluxo protegido de migração física da coluna pgvector e reindexação. No canto superior direito, um único menu de usuário substituirá os botões soltos de tema e desconexão e reunirá também o acesso à página Configurações.

## Technical Context

**Language/Version**: Python 3.14 com FastAPI, SQLAlchemy async e Pydantic v2; TypeScript 6.0 com Angular 22.0  
**Primary Dependencies**: FastAPI, SQLAlchemy/PostgreSQL, Pydantic Settings, httpx; Angular standalone components, HttpClient, Forms e Router  
**Storage**: PostgreSQL `app_config` existente, incluindo segredo cifrado; fallbacks e chave mestra em variáveis de ambiente  
**Testing**: pytest; Vitest/TestBed; `.venv/bin/python -m pytest`, `npm run typecheck`, `npm test -- --watch=false`, `npm run build`  
**Target Platform**: Backend Linux em Docker e portal Angular servido por Nginx; navegadores modernos  
**Project Type**: Aplicação web Angular + API FastAPI  
**Performance Goals**: Uma leitura curta de configuração por criação de cliente; endpoints de configuração dentro de 1 s em operação normal  
**Constraints**: Não editar `.env`/Docker em runtime; URL HTTP(S), modelos não vazios, chave API secreta; preservar autenticação Bearer e políticas de privacidade; dimensão exige migração exclusiva e reindexação  
**Scale/Scope**: Oito grupos de configuração, uma rota de API, uma página Angular, um menu de usuário, integração nos clientes e identidade de embeddings, operação de migração vetorial e documentação

## Constitution Check

### Pre-design gate

- **Code quality**: PASS — a resolução, cifragem, validação e transições ficam no serviço de configuração; a rota FastAPI somente transporta schemas e a página Angular usa o serviço HTTP existente.
- **Testing standards**: PASS — o plano prevê testes unitários para precedência/validação/cifragem, integração de API, migração vetorial e testes do componente; mantém PostgreSQL e SQLAlchemy async.
- **UX/accessibility**: PASS — a nova rota privada adota o shell, os estados e os padrões de formulário existentes, com labels, mensagens e foco acessíveis.
- **Performance**: PASS — a consulta é por chave primária de uma tabela pequena e ocorre apenas ao criar os clientes por requisição. A mudança de dimensão é operação administrativa assíncrona e controlada, nunca realizada no caminho de uma busca.
- **Technology/documentation**: PASS — permanece FastAPI, PostgreSQL e Angular; `doc/API.md` será atualizado por haver novos contratos HTTP.

### Post-design re-check

PASS esperado. O desenho usa o armazenamento existente, uma sobreposição de `Settings` por requisição, cifragem de segredo por chave mestra de ambiente e manutenção explícita para pgvector; não executa Docker remotamente.

## Project Structure

### Documentation (this feature)

```text
specs/022-configuracao-llm-portal/
├── spec.md
└── plan.md
```

### Source Code (repository root)

```text
backend/app/
├── api/
│   ├── dependencies.py                 # dependências async resolvidas com a configuração efetiva
│   └── routes/configuration.py         # GET/PUT e operação de dimensão
├── core/settings.py                    # fallbacks e chave mestra de ambiente tipados
├── schemas/configuration.py            # contratos Pydantic de leitura, atualização e manutenção
├── services/config.py                  # chaves, cifragem, validação, leitura/escrita e resolução efetiva
├── services/embedding_versions.py      # identidade e guard/migração de dimensão pgvector
├── services/embeddings.py              # recebe Settings efetivo por requisição
├── services/rag.py                     # recebe Settings efetivo por requisição
└── main.py                             # registra o novo router protegido

frontend/src/app/
├── app.routes.ts                       # rota privada /configuracoes
├── core/
│   ├── knowledge-api.service.ts        # métodos GET/PUT tipados
│   └── knowledge.types.ts               # tipos da configuração
├── features/configuration/
│   └── configuration-page.component.*   # formulário e estados da tela
└── layout/authenticated-layout.component.*      # menu de usuário: tema, Configurações e saída

tests/
├── test_config_service.py
└── test_configuration_api.py

doc/API.md                              # contrato HTTP e precedência dos valores
```

**Structure Decision**: manter precedência, persistência, cifragem e transições em `backend/app/services/config.py`; manter `configuration.py` como rota fina e `configuration-page` como feature isolada. `app_config` é estendida logicamente com novas chaves, sem tabela adicional. A única migration estrutural é a operação explicitamente confirmada para alteração de `vector(n)`.

## Implementation Approach

### 1. Formalizar configuração efetiva, segredo e persistência

- Definir chaves para `llm_provider`, URLs/modelos local e API, modelo de embeddings, dimensão e segredo API, sem colidir com `auth_token`.
- Criar schemas Pydantic para a configuração efetiva, com origem por valor e somente o booleano `api_key_configured`; o payload admite nova chave, mas nenhuma resposta a contém.
- Adicionar uma chave mestra obrigatória no ambiente do backend para cifrar/decifrar a chave de API. Falhar de modo explícito e seguro se a configuração persistida exigir segredo e a chave mestra estiver ausente ou inválida; garantir que logs e erros não revelem o valor.
- Normalizar espaços e validar provedor permitido, URLs HTTP(S), modelos não vazios, dimensão positiva e chave efetiva ao selecionar API. A API deve retornar 422 antes de iniciar escrita se a combinação for inválida.
- Implementar leitura que combina todos os registros de `app_config` com `Settings`, retornando valores efetivos e origem. A chave API é resolvida somente dentro do backend.
- Implementar upsert transacional para mudanças de configuração de runtime. Caso uma escrita falhe, rollback garante que o conjunto anterior continue ativo.

### 2. Aplicar sobreposição no runtime e preservar compatibilidade de embeddings

- Criar uma função assíncrona que recebe sessão e settings de ambiente, resolve a configuração persistida e devolve uma cópia tipada de `Settings` com todos os valores de IA substituídos.
- Transformar `get_embedding_client` e `get_answer_client` em dependências async com `AsyncSession`; elas construirão os clientes usando esses settings efetivos. As rotas de busca, ingestão, edição e resposta já consomem essas dependências, portanto novas requisições passam a respeitar o portal.
- Atualizar os pontos que chamam `active_embedding_identity` para usar a mesma configuração efetiva por requisição. Isso mantém busca, ingestão e reindexação coerentes após trocar provedor, modelo ou dimensão.
- Ao trocar provedor/modelo de embeddings, não descartar dados automaticamente: marcar/mostrar incompatibilidade e oferecer a operação de reindexação já existente. Respostas e busca novas passam a usar a identidade ativa.
- Revisar todos os locais que constroem clientes ou descrevem configuração de LLM (incluindo caminhos MCP/CLI, se aplicável) para garantir que o comportamento de API existente não seja afetado. Onde não houver sessão HTTP disponível, manter o ambiente como fallback explícito e documentado.
- Não alterar `docker-compose.yml`: ele continua mapeando `DOCKER_LOCAL_LLM_BASE_URL` para `LOCAL_LLM_BASE_URL` na criação do processo. O banco tem precedência somente depois que o portal salvar valores.

### 3. Oferecer manutenção controlada para `VECTOR_DIM`

- Separar atualização de dimensão das atualizações normais de runtime. A tela exibirá impacto, número de vetores afetados e confirmação textual explícita antes de iniciar a operação.
- Criar operação administrativa assíncrona com estado observável: bloquear temporariamente ingestão/busca dependentes de embeddings, invalidar embeddings existentes, alterar `knowledge_chunks.embedding` para `vector(n)`, reconstruir índices HNSW e reindexar os chunks com a nova dimensão.
- Garantir recuperação em caso de falha: status de manutenção e erro persistidos, sem publicar `VECTOR_DIM` como ativo enquanto banco/índice/reindexação não forem consistentes. Reutilizar a infraestrutura de operações/reindexação existente quando possível.
- Validar a dimensão retornada pelo novo provedor antes de finalizar; o guard de `assert_pgvector_dimension` continua impedindo inicialização com schema incompatível.

### 4. Expor o contrato HTTP protegido

- Criar `GET /api/v1/configuration/ai` para carregar valores efetivos, origem, estado de segredo e status de manutenção, sem chave API.
- Criar `PUT /api/v1/configuration/ai` para validar e substituir a configuração de runtime. A dimensão será rejeitada nesse endpoint quando diferente da ativa e direcionada ao fluxo protegido de manutenção.
- Criar endpoints de iniciar/consultar a mudança de dimensão sob autenticação, com confirmação explícita e estado operacional.
- Registrar o router em `main.py` com a mesma dependência `require_auth_token` das demais rotas privadas. Não retornar segredos nem criar acesso público.
- Atualizar `doc/API.md` com exemplos, códigos 200/401/409/422/503, precedência portal → ambiente, tratamento de segredo, reindexação/migração de dimensão e a semântica somente-de-boot de `DOCKER_LOCAL_LLM_BASE_URL`.

### 5. Criar a experiência de Configurações e o menu de usuário

- Adicionar rota autenticada `/configuracoes` e título de página coerente com as rotas existentes. O acesso será pelo menu de usuário do canto superior direito, não por um item adicional na sidebar.
- Adicionar tipos e métodos de leitura/atualização da configuração de IA e da manutenção vetorial ao serviço HTTP, sem espalhar URLs de API pelo componente.
- Implementar seções: Provedor e chat (seletor local/API e campos condicionais), Embeddings (modelo e impacto de compatibilidade) e Manutenção vetorial (dimensão ativa, risco, confirmação e progresso). Cada campo mostra valor efetivo e origem.
- Mostrar API key como campo de senha vazio com indicador “configurada/não configurada”, opção explícita de substituir/remover e sem pré-preencher o segredo.
- Bloquear envio inválido no cliente para feedback imediato, refletir mensagens 409/422/503 do servidor e exibir estados de carregamento, salvamento, sucesso e erro com `aria-live`. Após sucesso, atualizar campos e origens sem recarregar a rota.
- Manter a tela responsiva, com labels explícitos, foco visível e avisos claros sobre política de dados sensíveis, reindexação e indisponibilidade temporária na manutenção.
- Substituir os botões independentes de tema e desconectar em `authenticated-layout.component.*` por um botão de usuário com menu popover. O menu terá: alternância de tema com o estado atual, link Configurações e ação Desconectar, nessa ordem e separados visualmente quando necessário.
- Implementar estado e acessibilidade do menu: `aria-haspopup="menu"`, `aria-expanded`, foco inicial previsível, Escape, clique externo/backdrop conforme viewport, fechamento ao navegar/selecionar e retorno de foco ao botão quando o menu for apenas dispensado. O menu lateral de navegação continua independente.

### 6. Testar, documentar e verificar

- Cobrir serviço: fallback, precedência, normalização, combinações inválidas, cifragem/decifragem, ausência de vazamento, atomicidade e estado de manutenção.
- Cobrir API: autenticação obrigatória, leitura de fallback, atualização por provedor, omissão de segredo, 409 durante manutenção, 422 sem mudança parcial e fluxo confirmado de dimensão.
- Cobrir dependências: clientes e identidade de embeddings criados após atualização recebem os mesmos `Settings` efetivos; uma instância em execução preserva seu snapshot.
- Cobrir migração com PostgreSQL/pgvector: dimensão nova, índice recriado, embeddings invalidados/reindexados e recuperação de falha.
- Cobrir o componente Angular: campos condicionais, segredo mascarado, avisos de reindexação/manutenção, confirmação e progresso; também abertura/fechamento, teclado, tema, navegação e saída pelo menu de usuário.
- Executar quality gates backend e frontend e verificação manual em ambos os provedores, com e sem `/v1`, troca de embeddings e uma dimensão de teste.

## Data Model / API Implications

| Aspecto | Decisão |
|---|---|
| Persistência | Reuso de `app_config(key, value, updated_at)`. Valores operacionais em chaves próprias; chave API cifrada em registro separado. |
| Fallback | Ausência de registro usa os `Settings` correspondentes do ambiente. |
| Precedência | Valor salvo pelo portal → variáveis de processo. `DOCKER_LOCAL_LLM_BASE_URL` apenas fornece `LOCAL_LLM_BASE_URL` ao Compose no boot. |
| Segredo | Chave API cifrada com chave mestra exclusiva do backend; GET retorna somente estado configurado. |
| Leitura/escrita | `GET/PUT /api/v1/configuration/ai` para runtime; endpoints específicos e confirmados para dimensão. |
| Runtime | Dependências por requisição criam clientes e identidade de embeddings com snapshot consistente. |
| Dimensão | `VECTOR_DIM` somente torna-se ativa após migração de `vector(n)`, índices e reindexação concluídas. |

Exceto pela mudança explícita de dimensão, não há alteração estrutural: `Base.metadata.create_all` já cria `app_config` em instalações novas e instalações existentes já possuem a tabela. A dimensão requer migration operacional porque a coluna é hoje `vector(768)`.

## Test Strategy

- **Unitário backend**: normalização/validação, precedência, fallback, cifragem, upsert/rollback, cópia de `Settings` e transição de manutenção.
- **Integração backend**: autenticação, GET/PUT, omissão de segredo, 409/422, persistência e resolução nas dependências de LLM/embeddings.
- **PostgreSQL/pgvector**: migração de dimensão e recriação de índice, com reindexação e caso de falha.
- **Frontend**: TestBed de formulário condicional, segredo mascarado, manutenção e shell, HTTP simulado e transições acessíveis.
- **Manual**: configurar local e API; trocar embeddings e reindexar; executar troca controlada de dimensão em ambiente não produtivo; validar URL inválida, modelo vazio e chave ausente sem alterar valores anteriores.
- **Quality gates**: `.venv/bin/python -m pytest`, `cd frontend && npm run typecheck`, `npm test -- --watch=false`, `npm run build`.

## Rollout Order

1. Resolver/validar/cifrar/persistir configuração de runtime com testes unitários.
2. Ligar resolução aos clientes e à identidade de embeddings; validar local e API.
3. Implementar operação de dimensão, testes pgvector e integração com reindexação.
4. Publicar API protegida e documentação.
5. Entregar página, rota e menu de usuário com testes Angular.
6. Executar regressão completa e validar mudanças sem reinício, incluindo manutenção controlada.

## Risk Notes

- `get_settings()` é cacheado, então mudar somente o `.env` não atualiza um processo já iniciado. A resolução a partir do banco por requisição é essencial para o requisito de aplicação imediata.
- `DOCKER_LOCAL_LLM_BASE_URL` não existe dentro do backend como configuração runtime; é interpolado pelo Compose. Tentar editá-lo pelo portal não teria efeito e violaria o limite de não administrar Docker pela aplicação.
- Uma URL válida pode não estar acessível a partir da rede do container ou não servir o modelo informado. O escopo valida formato e preserva os erros 502/503 operacionais atuais; health check ativo de provedor fica fora do escopo.
- A aplicação usa o mesmo bearer token para todos os usuários autenticados. Se no futuro houver usuários não administrativos, a rota de escrita precisará de autorização por papel antes de ser exposta a eles.
- Trocar provedor afeta chat e embeddings no desenho atual; provedores externos ainda passam pelas políticas de conteúdo sensível. Trocar modelo/provedor de embeddings reduz resultados até reindexação, e a tela deve comunicar esse impacto.
- A chave mestra não pode ser persistida no banco nem compartilhada com frontend. Perda/rotação sem procedimento torna segredos existentes indecifráveis; o plano deve incluir procedimento de rotação e recuperação.
- Alterar dimensão é operação potencialmente longa e indisponibiliza embeddings. Ela deve ser executada primeiro em ambiente não produtivo, com backup e monitoramento; nunca como simples update de formulário.
- Menus popover são fáceis de tornar inacessíveis ou de sobrepor conteúdos em telas pequenas. O componente deve preservar foco, ter fechamento consistente e não reutilizar o estado do menu lateral.

## Complexity Tracking

Nenhuma violação da constituição identificada.
