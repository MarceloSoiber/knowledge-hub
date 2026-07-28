import { ComponentFixture, TestBed } from "@angular/core/testing";
import { provideRouter } from "@angular/router";
import { of } from "rxjs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { LibraryPageComponent } from "./library-page.component";

describe("LibraryPageComponent", () => {
  let fixture: ComponentFixture<LibraryPageComponent>;
  const sources = [
    { source_id: "a", title: "Ata de reunião", source_type: "text", uri: "ata", content_hash: "a", created_at: null, updated_at: null, categories: [{ id: 1, name: "Gestão" }], tags: [{ id: 3, name: "decisão" }], projects: [] },
    { source_id: "b", title: "Relatório técnico", source_type: "pdf", uri: "relatorio", content_hash: "b", created_at: null, updated_at: null, categories: [{ id: 2, name: "Produto" }], tags: [], projects: [] },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), { provide: KnowledgeApiService, useValue: { sources: () => of(sources) } }] });
    fixture = TestBed.createComponent(LibraryPageComponent);
    fixture.detectChanges();
  });
  afterEach(() => TestBed.resetTestingModule());

  it("filters loaded sources locally by accent-insensitive title and metadata", () => {
    const component = fixture.componentInstance;
    expect(component.filteredSources).toHaveLength(2);
    component.query = "reuniao";
    expect(component.filteredSources.map((source) => source.source_id)).toEqual(["a"]);
    component.query = "";
    component.categoryIds = [2];
    expect(component.filteredSources.map((source) => source.source_id)).toEqual(["b"]);
  });
});
