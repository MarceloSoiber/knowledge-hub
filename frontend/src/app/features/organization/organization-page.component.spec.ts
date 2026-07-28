import { ComponentFixture, TestBed } from "@angular/core/testing";
import { of } from "rxjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { OrganizationPageComponent } from "./organization-page.component";

describe("OrganizationPageComponent destructive actions", () => {
  const deleteCategory = vi.fn(() => of(undefined));
  const archiveProject = vi.fn(() => of({ id: 2, name: "hub", description: null, status: "archived", created_at: null, updated_at: null }));
  const catalog = { removeCategory: vi.fn(), upsertProject: vi.fn() };
  let fixture: ComponentFixture<OrganizationPageComponent>;

  beforeEach(() => {
    deleteCategory.mockClear();
    archiveProject.mockClear();
    catalog.removeCategory.mockClear();
    catalog.upsertProject.mockClear();
    TestBed.configureTestingModule({ providers: [
      { provide: KnowledgeApiService, useValue: { deleteCategory, archiveProject } },
      { provide: MetadataCatalogService, useValue: catalog },
    ] });
    fixture = TestBed.createComponent(OrganizationPageComponent);
  });

  afterEach(() => TestBed.resetTestingModule());

  it("does not delete a classification before confirmation", () => {
    const component = fixture.componentInstance;
    component.requestDelete("category", { id: 1, name: "docs" });
    component.cancelDelete();

    expect(component.deleteTarget).toBeNull();
    expect(deleteCategory).not.toHaveBeenCalled();
  });

  it("archives a project only after the status confirmation", () => {
    const component = fixture.componentInstance;
    component.requestStatus({ id: 2, name: "hub", description: null, status: "active", created_at: null, updated_at: null });
    component.changeStatus();

    expect(archiveProject).toHaveBeenCalledWith(2);
    expect(catalog.upsertProject).toHaveBeenCalledWith(expect.objectContaining({ status: "archived" }));
  });
});
