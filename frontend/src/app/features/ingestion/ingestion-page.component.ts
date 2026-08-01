import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectorRef, Component, ElementRef, OnInit, ViewChild, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { Category, KnowledgeTextIngestRequest, KnowledgeUploadResponse, MetadataSelection, Project, Tag } from "../../core/knowledge.types";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";
import { MetadataSelectorComponent } from "../../shared/metadata-selector/metadata-selector.component";

export type IngestionTab = "file" | "text";
export type IngestionStatus = "idle" | "validation-error" | "submitting" | "success" | "duplicate" | "request-error";

export interface IngestionState {
  status: IngestionStatus;
  message: string;
  result: KnowledgeUploadResponse | null;
  existingSourceId: string | null;
}

const emptySelection = (): MetadataSelection => ({ categoryIds: [], tagIds: [], projectIds: [] });
const idleState = (): IngestionState => ({ status: "idle", message: "", result: null, existingSourceId: null });
const allowedExtensions = new Set(["txt", "md", "pdf"]);
export const MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024;
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function validateFileDraft(file: File | null, selection: MetadataSelection): string {
  if (!file) return "Selecione um arquivo para enviar.";
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!allowedExtensions.has(extension)) return "Envie um arquivo .txt, .md ou .pdf.";
  if (file.size > MAX_FILE_SIZE_BYTES) return "O arquivo deve ter no máximo 100 MB.";
  if (!selection.categoryIds.length) return "Selecione pelo menos uma categoria.";
  return "";
}

export function buildTextIngestionRequest(title: string, content: string, selection: MetadataSelection): KnowledgeTextIngestRequest {
  return {
    title: title.trim(),
    content: content.trim(),
    category_ids: selection.categoryIds,
    ...(selection.tagIds.length ? { tag_ids: selection.tagIds } : {}),
    ...(selection.projectIds.length ? { project_ids: selection.projectIds } : {}),
  };
}

export function validateTextDraft(title: string, content: string, selection: MetadataSelection): string {
  if (!title.trim()) return "Informe um título para o texto.";
  if (title.trim().length > 255) return "O título deve ter no máximo 255 caracteres.";
  if (!content.trim()) return "Informe o conteúdo que será adicionado à base.";
  if (!selection.categoryIds.length) return "Selecione pelo menos uma categoria.";
  return "";
}

export function ingestionErrorMessage(status: number): string {
  if (status === 400 || status === 422) return "Revise os dados informados antes de tentar novamente.";
  if (status === 404) return "Um metadado não existe mais. Recarregue os metadados e revise a seleção.";
  if (status === 413) return "O arquivo excede o limite de 100 MB.";
  if (status === 502 || status === 503) return "Os embeddings estão indisponíveis no momento. Tente novamente em instantes.";
  return "Não foi possível concluir a ingestão. Verifique a conexão e tente novamente.";
}

export function duplicateSourceId(error: HttpErrorResponse): string | null {
  const candidate = error.error?.detail?.existing_source_id;
  return typeof candidate === "string" && uuidPattern.test(candidate) ? candidate : null;
}

@Component({
  selector: "kh-ingestion-page",
  imports: [FormsModule, RouterLink, ErrorStateComponent, LoadingStateComponent, MetadataSelectorComponent],
  templateUrl: "./ingestion-page.component.html",
  styleUrl: "./ingestion-page.component.css",
})
export class IngestionPageComponent implements OnInit {
  private readonly api = inject(KnowledgeApiService);
  private readonly catalog = inject(MetadataCatalogService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  @ViewChild("fileInput") private readonly fileInput?: ElementRef<HTMLInputElement>;

  activeTab: IngestionTab = "file";
  get metadataLoading(): boolean { return this.catalog.loading(); }
  get metadataError(): string { return this.catalog.error(); }
  get categories(): Category[] { return this.catalog.categories(); }
  get tags(): Tag[] { return this.catalog.tags(); }
  get projects(): Project[] { return this.catalog.activeProjects(); }

  file: File | null = null;
  isFileDragOver = false;
  fileSelection = emptySelection();
  fileState = idleState();

  textTitle = "";
  textContent = "";
  textSelection = emptySelection();
  textState = idleState();

  ngOnInit(): void { this.loadMetadata(); }

  loadMetadata(): void { this.catalog.load(true); }

  activateTab(tab: IngestionTab): void { this.activeTab = tab; }

  onTabKeydown(event: KeyboardEvent, tab: IngestionTab): void {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const nextTab = tab === "file" ? "text" : "file";
    this.activeTab = nextTab;
    (event.currentTarget as HTMLElement).parentElement?.querySelector<HTMLButtonElement>(`#${nextTab}-tab`)?.focus();
  }

  selectFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.setSelectedFile(input.files?.item(0) ?? null);
  }

  onFileDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isFileDragOver = true;
  }

  onFileDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isFileDragOver = false;
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    this.isFileDragOver = false;
    this.setSelectedFile(event.dataTransfer?.files.item(0) ?? null);
  }

  private setSelectedFile(file: File | null): void {
    this.file = file;
    if (this.fileState.status === "validation-error") this.fileState = idleState();
  }

  submitFile(): void {
    if (this.fileState.status === "submitting") return;
    const validationError = validateFileDraft(this.file, this.fileSelection);
    if (validationError) return this.setError("file", "validation-error", validationError);

    this.fileState = { ...idleState(), status: "submitting" };
    this.api.upload(this.file!, this.fileSelection.categoryIds, this.fileSelection.tagIds, this.fileSelection.projectIds).subscribe({
      next: (result) => {
        this.fileState = { ...idleState(), status: "success", result };
        this.file = null;
        this.fileSelection = emptySelection();
        if (this.fileInput) this.fileInput.nativeElement.value = "";
        this.changeDetectorRef.markForCheck();
      },
      error: (error: HttpErrorResponse) => this.handleRequestError("file", error),
    });
  }

  submitText(): void {
    if (this.textState.status === "submitting") return;
    const validationError = validateTextDraft(this.textTitle, this.textContent, this.textSelection);
    if (validationError) return this.setError("text", "validation-error", validationError);

    this.textState = { ...idleState(), status: "submitting" };
    this.api.ingestText(buildTextIngestionRequest(this.textTitle, this.textContent, this.textSelection)).subscribe({
      next: (result) => {
        this.textState = { ...idleState(), status: "success", result };
        this.textTitle = "";
        this.textContent = "";
        this.textSelection = emptySelection();
        this.changeDetectorRef.markForCheck();
      },
      error: (error: HttpErrorResponse) => this.handleRequestError("text", error),
    });
  }

  private handleRequestError(tab: IngestionTab, error: HttpErrorResponse): void {
    if (error.status === 409) {
      const existingSourceId = duplicateSourceId(error);
      this.setState(tab, { ...idleState(), status: "duplicate", existingSourceId, message: "Este conteúdo já existe na base. Nenhuma fonte foi sobrescrita." });
      return;
    }
    this.setError(tab, "request-error", ingestionErrorMessage(error.status));
  }

  private setError(tab: IngestionTab, status: Extract<IngestionStatus, "validation-error" | "request-error">, message: string): void {
    this.setState(tab, { ...idleState(), status, message });
  }

  private setState(tab: IngestionTab, state: IngestionState): void {
    if (tab === "file") this.fileState = state;
    else this.textState = state;
    this.changeDetectorRef.markForCheck();
  }
}
