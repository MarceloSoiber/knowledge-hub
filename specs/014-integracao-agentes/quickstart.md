# Quickstart: Integracao com Agentes

## 1. Verify Default Read-Only MCP Profile

```bash
MCP_WRITE_ENABLED=false .venv/bin/python -m pytest tests/test_mcp_knowledge.py -k scopes
```

Expected: the MCP profile exposes `knowledge:read` only and `ingest_text` remains denied.

## 2. Verify Agent Policy Text

```bash
.venv/bin/python -m pytest tests/test_agent_policy.py
```

Expected: policy examples cover search, no-search, reformulation, write confirmation and untrusted retrieved content.

## 3. Verify Prompt Injection Boundary

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py -k "prompt_injection or untrusted"
```

Expected: malicious retrieved text remains in context and does not replace system/developer instructions.

## 4. Verify Sensitive Category Blocking

```bash
SENSITIVE_CATEGORY_NAMES='["financeiro"]' LLM_PROVIDER=api .venv/bin/python -m pytest tests/test_knowledge_service.py -k sensitive
```

Expected: answer generation with retrieved `financeiro` content blocks before external provider use. The MVP blocks answer-generation context only; use a local provider for embeddings/ingestion of sensitive source content.

## 5. Full Feature Verification

```bash
.venv/bin/python -m pytest tests/test_agent_policy.py tests/test_mcp_knowledge.py tests/test_knowledge_service.py tests/test_knowledge_api_integration.py
```
