import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { provideHttpClient } from "@angular/common/http";
import { TestBed } from "@angular/core/testing";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { KnowledgeApiService } from "./knowledge-api.service";

describe("KnowledgeApiService ingestion", () => {
  let api: KnowledgeApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    api = TestBed.inject(KnowledgeApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    TestBed.resetTestingModule();
  });

  it("serializes a file and repeated metadata ids as FormData", () => {
    const file = new File(["conteúdo"], "notas.md", { type: "text/markdown" });
    api.upload(file, [1, 2], [3], [4, 5]).subscribe();

    const request = http.expectOne("/api/v1/knowledge/uploads");
    expect(request.request.method).toBe("POST");
    const body = request.request.body as FormData;
    expect(body.get("file")).toBe(file);
    expect(body.getAll("category_ids")).toEqual(["1", "2"]);
    expect(body.getAll("tag_ids")).toEqual(["3"]);
    expect(body.getAll("project_ids")).toEqual(["4", "5"]);
    request.flush({ source_id: "33333333-3333-4333-8333-333333333333", title: "notas.md", categories: [], tags: [], projects: [], chunks_created: 1 });
  });

  it("posts the typed text ingestion payload", () => {
    const payload = { title: "Ata", content: "Decisão", category_ids: [2], tag_ids: [3] };
    api.ingestText(payload).subscribe();

    const request = http.expectOne("/api/v1/knowledge/texts");
    expect(request.request.method).toBe("POST");
    expect(request.request.body).toEqual(payload);
    request.flush({ source_id: "33333333-3333-4333-8333-333333333333", title: "Ata", categories: [], tags: [], projects: [], chunks_created: 1 });
  });

  it("patches only the supplied source fields", () => {
    api.updateSource("33333333-3333-4333-8333-333333333333", { title: "Ata revisada", tag_ids: [2] }).subscribe();
    const request = http.expectOne("/api/v1/knowledge/sources/33333333-3333-4333-8333-333333333333");
    expect(request.request.method).toBe("PATCH");
    expect(request.request.body).toEqual({ title: "Ata revisada", tag_ids: [2] });
    request.flush({ source_id: "33333333-3333-4333-8333-333333333333", title: "Ata revisada", categories: [], tags: [], projects: [], source_type: "text", uri: "", content_hash: "hash", content: "texto", created_at: null, updated_at: null });
  });

  it("deletes a source only with the required confirmation query", () => {
    api.deleteSource("33333333-3333-4333-8333-333333333333").subscribe();
    const request = http.expectOne("/api/v1/knowledge/sources/33333333-3333-4333-8333-333333333333?confirm=true");
    expect(request.request.method).toBe("DELETE");
    request.flush(null);
  });
});
