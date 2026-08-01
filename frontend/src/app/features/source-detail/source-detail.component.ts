import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, Router, RouterLink } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { Category, KnowledgeSourceDetail, KnowledgeSourcePatchRequest, MetadataSelection, Project, Tag } from "../../core/knowledge.types";
import { ConfirmDialogComponent } from "../../shared/confirm-dialog/confirm-dialog.component";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";
import { MetadataSelectorComponent } from "../../shared/metadata-selector/metadata-selector.component";

interface SourceDraft { title: string; content: string; selection: MetadataSelection; }

@Component({
  selector: "kh-source-detail",
  imports: [FormsModule, RouterLink, ConfirmDialogComponent, ErrorStateComponent, LoadingStateComponent, MetadataSelectorComponent],
  templateUrl: "./source-detail.component.html",
  styleUrl: "./source-detail.component.css",
})
export class SourceDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(KnowledgeApiService);
  private readonly catalog = inject(MetadataCatalogService);
  private readonly router = inject(Router);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  source: KnowledgeSourceDetail | null = null;
  draft: SourceDraft = emptyDraft();
  get categories(): Category[] { return this.catalog.categories(); }
  get tags(): Tag[] { return this.catalog.tags(); }
  get projects(): Project[] { return this.catalog.activeProjects(); }
  loading = true;
  get loadingMetadata(): boolean { return this.catalog.loading(); }
  editing = false;
  saving = false;
  deleting = false;
  deleteDialogOpen = false;
  message = "";
  get metadataError(): string { return this.catalog.error(); }
  private sourceId = "";

  ngOnInit(): void {
    this.sourceId = this.route.snapshot.paramMap.get("sourceId") ?? "";
    if (!this.sourceId) { this.loading = false; this.message = "A fonte solicitada não é válida."; return; }
    this.loadSource();
  }

  get contentChanged(): boolean { return Boolean(this.source && this.draft.content.trim() !== this.source.content); }
  get hasChanges(): boolean { return Object.keys(this.patchPayload()).length > 0; }

  loadSource(): void {
    this.loading = true; this.message = "";
    this.api.source(this.sourceId).subscribe({
      next: (source) => { this.setSource(source); this.loading = false; this.changeDetectorRef.markForCheck(); },
      error: (error: HttpErrorResponse) => { this.loading = false; this.message = error.status === 404 ? "Esta fonte não existe mais." : "Não foi possível carregar a fonte."; this.changeDetectorRef.markForCheck(); },
    });
  }

  startEditing(): void {
    this.editing = true; this.message = "";
    if (!this.categories.length && !this.loadingMetadata) this.loadMetadata();
  }
  cancelEditing(): void { if (this.source) this.draft = draftFrom(this.source); this.editing = false; this.message = ""; }
  loadMetadata(): void { this.catalog.load(true); }
  save(): void {
    const payload = this.patchPayload();
    if (!Object.keys(payload).length) { this.message = "Não há alterações para salvar."; return; }
    this.saving = true; this.message = "";
    this.api.updateSource(this.sourceId, payload).subscribe({
      next: (source) => { this.setSource(source); this.saving = false; this.editing = false; this.message = "Alterações salvas."; this.changeDetectorRef.markForCheck(); },
      error: (error: HttpErrorResponse) => { this.saving = false; this.message = sourceError(error, "salvar"); this.changeDetectorRef.markForCheck(); },
    });
  }
  openDeleteDialog(): void { this.deleteDialogOpen = true; this.message = ""; }
  closeDeleteDialog(): void { if (!this.deleting) this.deleteDialogOpen = false; }
  delete(): void {
    this.deleting = true; this.message = "";
    this.api.deleteSource(this.sourceId).subscribe({
      next: async () => { await this.router.navigate(["/biblioteca"]); },
      error: (error: HttpErrorResponse) => { this.deleting = false; this.deleteDialogOpen = false; this.message = sourceError(error, "excluir"); this.changeDetectorRef.markForCheck(); },
    });
  }
  onSelectionChange(selection: MetadataSelection): void { this.draft = { ...this.draft, selection }; }

  private setSource(source: KnowledgeSourceDetail): void { this.source = source; this.draft = draftFrom(source); }
  private patchPayload(): KnowledgeSourcePatchRequest {
    if (!this.source) return {};
    const payload: KnowledgeSourcePatchRequest = {};
    const title = this.draft.title.trim(); const content = this.draft.content.trim();
    if (title && title !== this.source.title) payload.title = title;
    if (content && content !== this.source.content) payload.content = content;
    if (!sameIds(this.draft.selection.categoryIds, this.source.categories.map((item) => item.id))) payload.category_ids = this.draft.selection.categoryIds;
    if (!sameIds(this.draft.selection.tagIds, this.source.tags.map((item) => item.id))) payload.tag_ids = this.draft.selection.tagIds;
    if (!sameIds(this.draft.selection.projectIds, this.source.projects.map((item) => item.id))) payload.project_ids = this.draft.selection.projectIds;
    return payload;
  }
}

function emptyDraft(): SourceDraft { return { title: "", content: "", selection: { categoryIds: [], tagIds: [], projectIds: [] } }; }
function draftFrom(source: KnowledgeSourceDetail): SourceDraft { return { title: source.title, content: source.content, selection: { categoryIds: source.categories.map((item) => item.id), tagIds: source.tags.map((item) => item.id), projectIds: source.projects.map((item) => item.id) } }; }
function sameIds(a: number[], b: number[]): boolean { return a.length === b.length && a.every((id) => b.includes(id)); }
function sourceError(error: HttpErrorResponse, action: string): string {
  if (error.status === 404) return "Esta fonte não existe mais. Volte à Biblioteca para atualizar o acervo.";
  if (error.status === 409) return "Este conteúdo já existe em outra fonte. Revise o conteúdo antes de tentar novamente.";
  if (error.status === 400 || error.status === 422) return "Revise título, conteúdo e metadados antes de tentar novamente.";
  if (error.status === 502 || error.status === 503) return `O serviço de processamento está indisponível. Tente ${action} novamente.`;
  return `Não foi possível ${action} a fonte. Tente novamente.`;
}
