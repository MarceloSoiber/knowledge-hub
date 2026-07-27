import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { Category, Project, Tag } from "../../core/knowledge.types";
import { ConfirmDialogComponent } from "../../shared/confirm-dialog/confirm-dialog.component";
import { EmptyStateComponent } from "../../shared/empty-state/empty-state.component";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";

type Section = "categories" | "tags" | "projects";
type ClassificationKind = "category" | "tag";

@Component({
  selector: "kh-organization-page",
  imports: [FormsModule, RouterLink, ConfirmDialogComponent, EmptyStateComponent, ErrorStateComponent, LoadingStateComponent],
  templateUrl: "./organization-page.component.html",
  styleUrl: "./organization-page.component.css",
})
export class OrganizationPageComponent implements OnInit {
  readonly catalog = inject(MetadataCatalogService);
  private readonly api = inject(KnowledgeApiService);
  private readonly cdr = inject(ChangeDetectorRef);
  section: Section = "categories";
  projectStatus: "active" | "archived" = "active";
  classificationName = "";
  editingClassification: { kind: ClassificationKind; id: number } | null = null;
  projectName = "";
  projectDescription = "";
  editingProjectId: number | null = null;
  pending = false;
  message = "";
  deleteTarget: { kind: ClassificationKind; id: number; name: string } | null = null;
  statusTarget: Project | null = null;

  ngOnInit(): void { this.catalog.load(true); }
  get categories(): Category[] { return this.catalog.categories(); }
  get tags(): Tag[] { return this.catalog.tags(); }
  get projects(): Project[] { return this.catalog.projects().filter((item) => item.status === this.projectStatus); }

  selectSection(section: Section): void { this.section = section; this.message = ""; }
  editClassification(kind: ClassificationKind, item: Category | Tag): void { this.editingClassification = { kind, id: item.id }; this.classificationName = item.name; this.message = ""; }
  cancelClassification(): void { this.editingClassification = null; this.classificationName = ""; }
  saveClassification(kind: ClassificationKind): void {
    const name = this.classificationName.trim();
    if (!name || this.pending) { this.message = "Informe um nome para continuar."; return; }
    this.pending = true; this.message = "";
    const edit = this.editingClassification?.kind === kind ? this.editingClassification : null;
    const request = kind === "category"
      ? edit ? this.api.updateCategory(edit.id, { name }) : this.api.createCategory({ name })
      : edit ? this.api.updateTag(edit.id, { name }) : this.api.createTag({ name });
    request.subscribe({
      next: (item) => { if (kind === "category") this.catalog.upsertCategory(item); else this.catalog.upsertTag(item); this.cancelClassification(); this.pending = false; this.message = `${kind === "category" ? "Categoria" : "Tag"} salva.`; this.cdr.markForCheck(); },
      error: (error: HttpErrorResponse) => this.fail(error, "Não foi possível salvar. Revise o nome e tente novamente."),
    });
  }
  requestDelete(kind: ClassificationKind, item: Category | Tag): void { this.deleteTarget = { kind, id: item.id, name: item.name }; }
  cancelDelete(): void { if (!this.pending) this.deleteTarget = null; }
  deleteClassification(): void {
    const target = this.deleteTarget;
    if (!target || this.pending) return;
    this.pending = true;
    (target.kind === "category" ? this.api.deleteCategory(target.id) : this.api.deleteTag(target.id)).subscribe({
      next: () => { if (target.kind === "category") this.catalog.removeCategory(target.id); else this.catalog.removeTag(target.id); this.deleteTarget = null; this.pending = false; this.message = "Item excluído."; this.cdr.markForCheck(); },
      error: (error: HttpErrorResponse) => { this.deleteTarget = null; this.fail(error, "Não foi possível excluir o item.", true); },
    });
  }

  editProject(project: Project): void { this.editingProjectId = project.id; this.projectName = project.name; this.projectDescription = project.description ?? ""; this.message = ""; }
  cancelProject(): void { this.editingProjectId = null; this.projectName = ""; this.projectDescription = ""; }
  saveProject(): void {
    const name = this.projectName.trim();
    if (!name || this.pending) { this.message = "Informe o nome do projeto."; return; }
    this.pending = true; this.message = "";
    const payload = { name, description: this.projectDescription.trim() || null };
    const request = this.editingProjectId ? this.api.updateProject(this.editingProjectId, payload) : this.api.createProject(payload);
    request.subscribe({ next: (project) => { this.catalog.upsertProject(project); this.cancelProject(); this.pending = false; this.message = "Projeto salvo."; this.cdr.markForCheck(); }, error: (error: HttpErrorResponse) => this.fail(error, "Não foi possível salvar o projeto. Revise os dados e tente novamente.") });
  }
  requestStatus(project: Project): void { this.statusTarget = project; }
  cancelStatus(): void { if (!this.pending) this.statusTarget = null; }
  changeStatus(): void {
    const project = this.statusTarget;
    if (!project || this.pending) return;
    this.pending = true;
    const request = project.status === "active" ? this.api.archiveProject(project.id) : this.api.reactivateProject(project.id);
    request.subscribe({ next: (updated) => { this.catalog.upsertProject(updated); this.statusTarget = null; this.pending = false; this.message = updated.status === "archived" ? "Projeto arquivado." : "Projeto reativado."; this.cdr.markForCheck(); }, error: (error: HttpErrorResponse) => { this.statusTarget = null; this.fail(error, "Não foi possível alterar o status do projeto."); } });
  }

  private fail(error: HttpErrorResponse, fallback: string, deleting = false): void {
    this.pending = false;
    this.message = deleting && error.status === 409 ? "Este item está em uso. Reclassifique as fontes antes de removê-lo." : error.status === 404 ? "O item não existe mais. Recarregue a lista." : error.status === 409 ? "Já existe um item com esse nome. Escolha outro nome." : error.status === 502 || error.status === 503 ? "O serviço está indisponível. Tente novamente em instantes." : fallback;
    this.cdr.markForCheck();
  }
}
