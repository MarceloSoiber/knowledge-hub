import { HttpErrorResponse } from "@angular/common/http";
import { describe, expect, it } from "vitest";

import { MAX_FILE_SIZE_BYTES, buildTextIngestionRequest, duplicateSourceId, ingestionErrorMessage, validateFileDraft, validateTextDraft } from "./ingestion-page.component";

const selection = { categoryIds: [2], tagIds: [3], projectIds: [4] };

describe("ingestion page helpers", () => {
  it("validates files before a request", () => {
    const validFile = new File(["conteúdo"], "notas.MD", { type: "text/markdown" });
    expect(validateFileDraft(validFile, selection)).toBe("");
    expect(validateFileDraft(null, selection)).toContain("Selecione");
    expect(validateFileDraft(new File(["x"], "notas.docx"), selection)).toContain(".txt");
    expect(validateFileDraft(validFile, { ...selection, categoryIds: [] })).toContain("categoria");
    expect(validateFileDraft({ name: "grande.pdf", size: MAX_FILE_SIZE_BYTES + 1 } as File, selection)).toContain("100 MB");
  });

  it("builds the text payload without empty optional arrays", () => {
    expect(buildTextIngestionRequest("  Ata  ", "  Decisão  ", { categoryIds: [2], tagIds: [], projectIds: [] })).toEqual({ title: "Ata", content: "Decisão", category_ids: [2] });
    expect(buildTextIngestionRequest("Ata", "Decisão", selection)).toEqual({ title: "Ata", content: "Decisão", category_ids: [2], tag_ids: [3], project_ids: [4] });
  });

  it("validates title, content and required categories", () => {
    expect(validateTextDraft(" ", "conteúdo", selection)).toContain("título");
    expect(validateTextDraft("Título", " ", selection)).toContain("conteúdo");
    expect(validateTextDraft("Título", "conteúdo", { ...selection, categoryIds: [] })).toContain("categoria");
    expect(validateTextDraft("x".repeat(256), "conteúdo", selection)).toContain("255");
  });

  it("uses structured UUIDs only for duplicate links", () => {
    const uuid = "33333333-3333-4333-8333-333333333333";
    expect(duplicateSourceId(new HttpErrorResponse({ status: 409, error: { detail: { existing_source_id: uuid } } }))).toBe(uuid);
    expect(duplicateSourceId(new HttpErrorResponse({ status: 409, error: { detail: { existing_source_id: "untrusted" } } }))).toBeNull();
  });

  it("maps request errors without exposing API details", () => {
    expect(ingestionErrorMessage(413)).toContain("100 MB");
    expect(ingestionErrorMessage(503)).toContain("indisponíveis");
    expect(ingestionErrorMessage(500)).not.toContain("detail");
  });
});
