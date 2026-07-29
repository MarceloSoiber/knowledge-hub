import { ComponentFixture, TestBed } from "@angular/core/testing";
import { provideRouter } from "@angular/router";
import { of, throwError } from "rxjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { KnowledgeChunk, KnowledgeSource } from "../../core/knowledge.types";
import { compareRecentSources, HomeComponent } from "./home.component";

const source = (sourceId: string, title: string, createdAt: string | null, updatedAt: string | null = null): KnowledgeSource => ({
  source_id: sourceId,
  title,
  source_type: "text",
  uri: `text:${title}`,
  content_hash: "hash",
  created_at: createdAt,
  updated_at: updatedAt,
  categories: [],
  tags: [],
  projects: [],
});

describe("HomeComponent", () => {
  let fixture: ComponentFixture<HomeComponent>;
  let api: { sources: ReturnType<typeof vi.fn>; categories: ReturnType<typeof vi.fn>; tags: ReturnType<typeof vi.fn>; projects: ReturnType<typeof vi.fn>; search: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    api = {
      sources: vi.fn(() => of([source("old", "Ata", "2026-01-01T10:00:00Z"), source("new", "Relatório", "2026-02-01T10:00:00Z")])),
      categories: vi.fn(() => of([{ id: 1, name: "produto" }])),
      tags: vi.fn(() => of([{ id: 2, name: "prioridade" }, { id: 3, name: "interno" }])),
      projects: vi.fn(() => of([
        { id: 4, name: "ativo", description: null, status: "active", created_at: null, updated_at: null },
        { id: 5, name: "arquivado", description: null, status: "archived", created_at: null, updated_at: null },
        { id: 6, name: "ativo dois", description: null, status: "active", created_at: null, updated_at: null },
      ])),
      search: vi.fn(() => of({ query: "decisão", limit: 4, results: [searchResult()] })),
    };
    TestBed.configureTestingModule({ providers: [provideRouter([]), { provide: KnowledgeApiService, useValue: api }] });
    fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
  });

  afterEach(() => TestBed.resetTestingModule());

  it("loads each collection and derives the five dashboard metrics", () => {
    const component = fixture.componentInstance;
    expect(api.sources).toHaveBeenCalledOnce();
    expect(api.categories).toHaveBeenCalledOnce();
    expect(api.tags).toHaveBeenCalledOnce();
    expect(api.projects).toHaveBeenCalledOnce();
    expect(component.metrics.map((metric) => [metric.label, metric.value])).toEqual([
      ["Fontes", 2], ["Categorias", 1], ["Tags", 2], ["Projetos ativos", 2], ["Projetos arquivados", 1],
    ]);
    expect(component.recentSources.map((item) => item.source_id)).toEqual(["new", "old"]);
  });

  it("sorts valid dates first and uses title then id as a deterministic fallback", () => {
    const items = [
      source("z", "Zeta", null),
      source("a", "Alpha", "invalid-date"),
      source("updated", "Atualizada", null, "2026-01-03T10:00:00Z"),
      source("created", "Criada", "2026-01-04T10:00:00Z"),
      source("b", "Mesmo", null),
      source("c", "Mesmo", null),
    ];
    expect(items.sort(compareRecentSources).map((item) => item.source_id)).toEqual(["created", "updated", "a", "b", "c", "z"]);
  });

  it("keeps the action links available and exposes a recoverable source error", () => {
    api.sources.mockReturnValueOnce(throwError(() => new Error("offline")));
    fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    expect(component.sourcesState.error).toContain("fontes recentes");
    const links = Array.from(fixture.nativeElement.querySelectorAll("a"), (link: HTMLAnchorElement) => link.getAttribute("href"));
    expect(links).toContain("/busca");
    expect(links).toContain("/perguntar");
    expect(links).toContain("/ingestao");
  });

  it("searches in place and presents the matching source without navigating away", () => {
    const component = fixture.componentInstance;
    component.searchQuery = "decisão";
    component.search();
    fixture.detectChanges();

    expect(api.search).toHaveBeenCalledWith({ query: "decisão", limit: 4 });
    expect(component.searchStatus).toBe("success");
    expect(fixture.nativeElement.textContent).toContain("Resultados para “decisão”");
    expect(fixture.nativeElement.textContent).toContain("Ata de decisão");
  });

  it("shows the first-ingestion call to action for an empty source list", () => {
    api.sources.mockReturnValueOnce(of([]));
    fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("Nenhuma fonte no acervo");
    expect(fixture.nativeElement.textContent).toContain("Iniciar ingestão");
  });
});

function searchResult(): KnowledgeChunk {
  return {
    id: 1,
    source_id: "source-1",
    source_title: "Ata de decisão",
    source_type: "text",
    uri: "text:ata",
    categories: [], tags: [], projects: [],
    location: { chunk_index: 0, page: null, section: "Decisões", start_char: 0, end_char: 48 },
    content: "A equipe aprovou o plano de implantação.",
    score: 0.9,
    metadata: {},
  };
}
