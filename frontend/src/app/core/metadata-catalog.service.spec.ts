import { TestBed } from "@angular/core/testing";
import { afterEach, describe, expect, it } from "vitest";
import { of } from "rxjs";

import { KnowledgeApiService } from "./knowledge-api.service";
import { MetadataCatalogService } from "./metadata-catalog.service";

describe("MetadataCatalogService", () => {
  afterEach(() => TestBed.resetTestingModule());

  it("keeps canonical metadata and derives active projects", () => {
    TestBed.configureTestingModule({ providers: [{ provide: KnowledgeApiService, useValue: {
      categories: () => of([{ id: 2, name: "docs" }]),
      tags: () => of([{ id: 3, name: "rag" }]),
      projects: () => of([
        { id: 1, name: "old", description: null, status: "archived", created_at: null, updated_at: null },
        { id: 4, name: "hub", description: null, status: "active", created_at: null, updated_at: null },
      ]),
    } }] });
    const catalog = TestBed.inject(MetadataCatalogService);
    catalog.load();
    expect(catalog.categories()).toEqual([{ id: 2, name: "docs" }]);
    expect(catalog.tags()).toEqual([{ id: 3, name: "rag" }]);
    expect(catalog.activeProjects().map((project) => project.id)).toEqual([4]);
    catalog.upsertProject({ id: 4, name: "hub", description: null, status: "archived", created_at: null, updated_at: null });
    expect(catalog.activeProjects()).toEqual([]);
  });
});
