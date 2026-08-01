import { ComponentFixture, TestBed } from "@angular/core/testing";
import { ActivatedRoute, Router } from "@angular/router";
import { of } from "rxjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { SourceDetailComponent } from "./source-detail.component";

describe("SourceDetailComponent deletion confirmation", () => {
  const deleteSource = vi.fn(() => of(undefined));
  const source = vi.fn(() => of({
    source_id: "33333333-3333-4333-8333-333333333333", title: "Ata", content: "Conteúdo", source_type: "text", uri: "text:Ata", content_hash: "hash",
    created_at: null, updated_at: null, categories: [], tags: [], projects: [],
  }));
  let fixture: ComponentFixture<SourceDetailComponent>;

  beforeEach(() => {
    deleteSource.mockClear();
    TestBed.configureTestingModule({ providers: [
      { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => "33333333-3333-4333-8333-333333333333" } } } },
      { provide: Router, useValue: { navigate: vi.fn(() => Promise.resolve(true)) } },
      { provide: KnowledgeApiService, useValue: { deleteSource, source } },
      { provide: MetadataCatalogService, useValue: {} },
    ] });
    fixture = TestBed.createComponent(SourceDetailComponent);
  });

  afterEach(() => TestBed.resetTestingModule());

  it("does not send DELETE when the confirmation is closed", () => {
    const component = fixture.componentInstance;
    component.openDeleteDialog();
    component.closeDeleteDialog();

    expect(component.deleteDialogOpen).toBe(false);
    expect(deleteSource).not.toHaveBeenCalled();
  });

  it("sends DELETE only after confirmation", () => {
    const component = fixture.componentInstance;
    component.ngOnInit();
    component.openDeleteDialog();
    component.delete();

    expect(deleteSource).toHaveBeenCalledWith("33333333-3333-4333-8333-333333333333");
  });
});
