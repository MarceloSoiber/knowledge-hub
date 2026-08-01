import { HttpErrorResponse } from "@angular/common/http";
import { DecimalPipe } from "@angular/common";
import { ChangeDetectorRef, Component, OnDestroy, OnInit, effect, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";
import { Subject, of } from "rxjs";
import { catchError, debounceTime, distinctUntilChanged, switchMap, takeUntil } from "rxjs/operators";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { MetadataCatalogService } from "../../core/metadata-catalog.service";
import { Category, KnowledgeAnswerRequest, KnowledgeAnswerResponse, KnowledgeChunk, Project, Tag } from "../../core/knowledge.types";

type AnswerStatus = "idle" | "loading" | "success" | "success-without-sources" | "error";

export interface AnswerHistoryEntry {
  id: string;
  query: string;
  answer: string;
  sources: KnowledgeChunk[];
  includeMatchReasons: boolean;
}

export function buildAnswerRequest(
  query: string,
  limit: number,
  minScore: number | null,
  categories: Category[],
  tags: Tag[],
  projects: Project[],
  includeMatchReasons: boolean,
): KnowledgeAnswerRequest {
  return {
    query: query.trim(),
    limit,
    ...(categories.length ? { category_ids: categories.map(({ id }) => id) } : {}),
    ...(tags.length ? { tag_ids: tags.map(({ id }) => id) } : {}),
    ...(projects.length ? { project_ids: projects.map(({ id }) => id) } : {}),
    ...(minScore !== null ? { min_score: minScore } : {}),
    ...(includeMatchReasons ? { include_match_reasons: true } : {}),
  };
}

export function answerErrorMessage(status: number): string {
  if (status === 403) return "A resposta foi bloqueada por conteúdo sensível. Reformule a pergunta e tente novamente.";
  if (status === 404) return "Um filtro não existe mais. Recarregue os filtros e tente novamente.";
  if (status === 422) return "Revise a pergunta e os filtros informados antes de tentar novamente.";
  if (status === 502 || status === 503) return "Embeddings ou o modelo de resposta estão indisponíveis no momento. Tente novamente em instantes.";
  return "Não foi possível concluir a pergunta. Verifique a conexão e tente novamente.";
}

export function referencesText(sources: KnowledgeChunk[]): string {
  return sources.map((source) => {
    const location = [source.location.page ? `Página ${source.location.page}` : "", source.location.section ?? "", `Trecho ${source.location.chunk_index + 1}`]
      .filter(Boolean)
      .join(" · ");
    return `${source.source_title}\n${location}\n${source.content}`;
  }).join("\n\n");
}

export function createAnswerHistoryId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

@Component({
  selector: "kh-ask-page",
  imports: [DecimalPipe, FormsModule, RouterLink],
  templateUrl: "./ask-page.component.html",
  styleUrl: "./ask-page.component.css",
})
export class AskPageComponent implements OnInit, OnDestroy {
  private readonly api = inject(KnowledgeApiService);
  private readonly catalog = inject(MetadataCatalogService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private readonly tagQuery$ = new Subject<string>();

  query = "";
  limit = 5;
  minScore: number | null = null;
  includeMatchReasons = false;
  categoryOptions: Category[] = [];
  projectOptions: Project[] = [];
  tagOptions: Tag[] = [];
  selectedCategories: Category[] = [];
  selectedProjects: Project[] = [];
  selectedTags: Tag[] = [];
  tagQuery = "";
  history: AnswerHistoryEntry[] = [];
  status: AnswerStatus = "idle";
  message = "";
  metadataError = "";
  copyFeedback = "";

  constructor() {
    effect(() => { this.categoryOptions = this.catalog.categories(); this.projectOptions = this.catalog.activeProjects(); this.metadataError = this.catalog.error(); });
  }

  ngOnInit(): void {
    this.loadMetadata();
    this.tagQuery$
      .pipe(
        debounceTime(250),
        distinctUntilChanged(),
        switchMap((query) => query.trim() ? this.api.tagAutocomplete(query.trim()).pipe(catchError(() => of([]))) : of([])),
        takeUntil(this.destroy$),
      )
      .subscribe((tags) => {
        this.tagOptions = tags.filter((tag) => !this.selectedTags.some((selected) => selected.id === tag.id));
        this.changeDetectorRef.markForCheck();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMetadata(): void {
    this.catalog.load(true);
  }

  ask(): void {
    const normalizedQuery = this.query.trim();
    if (!normalizedQuery) return this.setValidationError("Informe uma pergunta para consultar a base.");
    if (!Number.isInteger(this.limit) || this.limit < 1 || this.limit > 20) return this.setValidationError("O limite deve ser um número inteiro entre 1 e 20.");
    if (this.minScore !== null && (this.minScore < 0 || this.minScore > 1)) return this.setValidationError("O score mínimo deve ficar entre 0 e 1.");

    this.status = "loading";
    this.message = "";
    this.copyFeedback = "";
    this.api.answer(buildAnswerRequest(normalizedQuery, this.limit, this.minScore, this.selectedCategories, this.selectedTags, this.selectedProjects, this.includeMatchReasons)).subscribe({
      next: (response) => this.addAnswer(response),
      error: (error: HttpErrorResponse) => {
        this.status = "error";
        this.message = answerErrorMessage(error.status);
        this.changeDetectorRef.markForCheck();
      },
    });
  }

  onTagInput(): void { this.tagQuery$.next(this.tagQuery); }
  addCategory(id: string): void { this.addSelected(this.categoryOptions, this.selectedCategories, id, (items) => this.selectedCategories = items); }
  addProject(id: string): void { this.addSelected(this.projectOptions, this.selectedProjects, id, (items) => this.selectedProjects = items); }
  addTag(tag: Tag): void {
    if (!this.selectedTags.some((item) => item.id === tag.id)) this.selectedTags = [...this.selectedTags, tag];
    this.tagQuery = "";
    this.tagOptions = [];
  }
  removeCategory(id: number): void { this.selectedCategories = this.selectedCategories.filter((item) => item.id !== id); }
  removeProject(id: number): void { this.selectedProjects = this.selectedProjects.filter((item) => item.id !== id); }
  removeTag(id: number): void { this.selectedTags = this.selectedTags.filter((item) => item.id !== id); }

  location(source: KnowledgeChunk): string {
    return [source.location.page ? `Página ${source.location.page}` : "", source.location.section ?? "", `Trecho ${source.location.chunk_index + 1}`].filter(Boolean).join(" · ");
  }

  async copyAnswer(entry: AnswerHistoryEntry): Promise<void> { await this.copy(entry.answer, "Resposta copiada."); }
  async copyReferences(entry: AnswerHistoryEntry): Promise<void> {
    if (!entry.sources.length) {
      this.copyFeedback = "Esta resposta não tem referências para copiar.";
      return;
    }
    await this.copy(referencesText(entry.sources), "Referências copiadas.");
  }

  private addAnswer(response: KnowledgeAnswerResponse): void {
    this.history = [{ id: createAnswerHistoryId(), query: response.query, answer: response.answer, sources: response.sources, includeMatchReasons: this.includeMatchReasons }, ...this.history];
    this.status = response.sources.length ? "success" : "success-without-sources";
    this.changeDetectorRef.markForCheck();
  }

  private setValidationError(message: string): void {
    this.status = "error";
    this.message = message;
  }

  private addSelected<T extends Category>(options: T[], selected: T[], id: string, update: (items: T[]) => void): void {
    const item = options.find((option) => option.id === Number(id));
    if (item && !selected.some((value) => value.id === item.id)) update([...selected, item]);
  }

  private async copy(text: string, successMessage: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
      this.copyFeedback = successMessage;
    } catch {
      this.copyFeedback = "Não foi possível copiar. Selecione o texto manualmente.";
    }
  }
}
