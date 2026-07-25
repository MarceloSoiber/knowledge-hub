import { HttpErrorResponse } from "@angular/common/http";
import { DecimalPipe } from "@angular/common";
import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";
import { Subject, forkJoin, of } from "rxjs";
import { catchError, debounceTime, distinctUntilChanged, switchMap, takeUntil } from "rxjs/operators";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { Category, KnowledgeSearchResult, Project, SearchRequest, Tag } from "../../shared/models/knowledge.models";

type SearchStatus = "idle" | "loading" | "success" | "error";

@Component({
  selector: "kh-search-page",
  imports: [DecimalPipe, FormsModule, RouterLink],
  templateUrl: "./search-page.component.html",
  styleUrl: "./search-page.component.css",
})
export class SearchPageComponent implements OnInit, OnDestroy {
  private readonly api = inject(KnowledgeApiService);
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
  allTags: Tag[] = [];
  tagQuery = "";
  results: KnowledgeSearchResult[] = [];
  status: SearchStatus = "idle";
  message = "";
  metadataError = "";

  ngOnInit(): void {
    this.loadMetadata();
    this.tagQuery$
      .pipe(
        debounceTime(250),
        distinctUntilChanged(),
        switchMap((query) => query.trim().length > 0 ? this.api.autocompleteTags(query.trim()) : of([])),
        takeUntil(this.destroy$),
      )
      .subscribe({
        next: (tags) => {
          this.tagOptions = tags.filter((tag) => !this.selectedTags.some((selected) => selected.id === tag.id));
          this.changeDetectorRef.markForCheck();
        },
        error: () => {
          this.tagOptions = [];
          this.changeDetectorRef.markForCheck();
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMetadata(): void {
    this.metadataError = "";
    forkJoin({ categories: this.api.categories(), tags: this.api.tags(), projects: this.api.projects() }).subscribe({
      next: ({ categories, tags, projects }) => {
        this.categoryOptions = categories;
        this.allTags = tags;
        this.projectOptions = projects;
        this.changeDetectorRef.markForCheck();
      },
      error: () => {
        this.metadataError = "Não foi possível carregar os filtros. Tente recarregá-los.";
        this.changeDetectorRef.markForCheck();
      },
    });
  }

  search(): void {
    const normalizedQuery = this.query.trim();
    if (!normalizedQuery) {
      this.status = "error";
      this.message = "Informe uma consulta para buscar.";
      return;
    }
    if (!Number.isInteger(this.limit) || this.limit < 1 || this.limit > 50) {
      this.status = "error";
      this.message = "O limite deve ser um número inteiro entre 1 e 50.";
      return;
    }
    if (this.minScore !== null && (this.minScore < 0 || this.minScore > 1)) {
      this.status = "error";
      this.message = "O score mínimo deve ficar entre 0 e 1.";
      return;
    }

    this.status = "loading";
    this.message = "";
    const request: SearchRequest = {
      query: normalizedQuery,
      limit: this.limit,
      ...(this.selectedCategories.length ? { category_ids: this.selectedCategories.map((item) => item.id) } : {}),
      ...(this.selectedTags.length ? { tag_ids: this.selectedTags.map((item) => item.id) } : {}),
      ...(this.selectedProjects.length ? { project_ids: this.selectedProjects.map((item) => item.id) } : {}),
      ...(this.minScore !== null ? { min_score: this.minScore } : {}),
      ...(this.includeMatchReasons ? { include_match_reasons: true } : {}),
    };

    this.api.search(request).subscribe({
      next: (response) => {
        this.results = response.results;
        this.status = "success";
        this.changeDetectorRef.markForCheck();
      },
      error: (error: HttpErrorResponse) => {
        this.status = "error";
        this.message = this.requestErrorMessage(error.status);
        this.changeDetectorRef.markForCheck();
      },
    });
  }

  onTagInput(): void {
    this.tagQuery$.next(this.tagQuery);
  }

  addCategory(id: string): void {
    const category = this.categoryOptions.find((item) => item.id === Number(id));
    if (category && !this.selectedCategories.some((item) => item.id === category.id)) this.selectedCategories = [...this.selectedCategories, category];
  }

  addProject(id: string): void {
    const project = this.projectOptions.find((item) => item.id === Number(id));
    if (project && !this.selectedProjects.some((item) => item.id === project.id)) this.selectedProjects = [...this.selectedProjects, project];
  }

  addTag(tag: Tag): void {
    if (!this.selectedTags.some((item) => item.id === tag.id)) this.selectedTags = [...this.selectedTags, tag];
    this.tagQuery = "";
    this.tagOptions = [];
  }

  removeCategory(id: number): void { this.selectedCategories = this.selectedCategories.filter((item) => item.id !== id); }
  removeProject(id: number): void { this.selectedProjects = this.selectedProjects.filter((item) => item.id !== id); }
  removeTag(id: number): void { this.selectedTags = this.selectedTags.filter((item) => item.id !== id); }

  location(result: KnowledgeSearchResult): string {
    const parts = [result.location.page ? `página ${result.location.page}` : "", result.location.section ?? "", `trecho ${result.location.chunk_index + 1}`];
    return parts.filter(Boolean).join(" · ");
  }

  private requestErrorMessage(status: number): string {
    if (status === 404) return "Um filtro não existe mais. Recarregue os filtros e tente novamente.";
    if (status === 422) return "Revise a consulta e os filtros informados antes de tentar novamente.";
    if (status === 502 || status === 503) return "A busca ou os embeddings estão indisponíveis no momento. Tente novamente em instantes.";
    return "Não foi possível concluir a busca. Verifique a conexão e tente novamente.";
  }
}
