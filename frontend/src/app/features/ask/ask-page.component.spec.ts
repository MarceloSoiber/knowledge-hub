import { describe, expect, it } from "vitest";

import { answerErrorMessage, buildAnswerRequest, referencesText } from "./ask-page.component";

const source = {
  id: 1, source_id: "source-uuid", source_title: "Decisões.md", source_type: "text", uri: "text:Decisões.md",
  categories: [], tags: [], projects: [], location: { chunk_index: 0, page: 3, section: "Contexto", start_char: 0, end_char: 20 },
  content: "Uma decisão importante.", score: 0.8, metadata: {},
};

describe("ask page helpers", () => {
  it("serializes only meaningful filters for the answer contract", () => {
    expect(buildAnswerRequest("  Qual decisão?  ", 5, null, [], [], [], false)).toEqual({ query: "Qual decisão?", limit: 5 });
    expect(buildAnswerRequest("Pergunta", 10, .35, [{ id: 1, name: "docs" }], [{ id: 2, name: "rag" }], [{ id: 3, name: "Hub", description: null, status: "active", created_at: null, updated_at: null }], true)).toEqual({ query: "Pergunta", limit: 10, min_score: .35, category_ids: [1], tag_ids: [2], project_ids: [3], include_match_reasons: true });
  });

  it("uses safe messages for expected answer errors", () => {
    expect(answerErrorMessage(403)).toContain("conteúdo sensível");
    expect(answerErrorMessage(502)).toContain("indisponíveis");
    expect(answerErrorMessage(500)).not.toContain("detail");
  });

  it("formats references without internal identifiers or URI", () => {
    const text = referencesText([source]);
    expect(text).toContain("Decisões.md");
    expect(text).toContain("Página 3 · Contexto · Trecho 1");
    expect(text).not.toContain("source-uuid");
    expect(text).not.toContain("text:");
  });
});
