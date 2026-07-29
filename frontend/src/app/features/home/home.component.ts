import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";
import { Observable } from "rxjs";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { Category, KnowledgeChunk, KnowledgeSource, Project, Tag } from "../../core/knowledge.types";
import { EmptyStateComponent } from "../../shared/empty-state/empty-state.component";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";

interface CollectionState<T> {
  items: T[];
  loading: boolean;
  error: string;
}

interface Metric {
  label: string;
  value: number;
  loading: boolean;
  error: string;
  retry: () => void;
}

type SearchStatus = "idle" | "loading" | "success" | "error";

@Component({
  selector: "kh-home",
  imports: [FormsModule, RouterLink, LoadingStateComponent, ErrorStateComponent, EmptyStateComponent],
  templateUrl: "./home.component.html",
  styleUrl: "./home.component.css",
})
export class HomeComponent implements OnInit {
  private readonly api = inject(KnowledgeApiService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);

  readonly sourcesState: CollectionState<KnowledgeSource> = emptyState();
  readonly categoriesState: CollectionState<Category> = emptyState();
  readonly tagsState: CollectionState<Tag> = emptyState();
  readonly projectsState: CollectionState<Project> = emptyState();
  searchQuery = "";
  searchResults: KnowledgeChunk[] = [];
  searchStatus: SearchStatus = "idle";
  searchMessage = "";

  ngOnInit(): void {
    this.loadSources();
    this.loadCategories();
    this.loadTags();
    this.loadProjects();
  }

  get metrics(): Metric[] {
    return [
      metric("Fontes", this.sourcesState, () => this.loadSources()),
      metric("Categorias", this.categoriesState, () => this.loadCategories()),
      metric("Tags", this.tagsState, () => this.loadTags()),
      {
        label: "Projetos ativos",
        value: this.projectsState.items.filter((project) => project.status === "active").length,
        loading: this.projectsState.loading,
        error: this.projectsState.error,
        retry: () => this.loadProjects(),
      },
      {
        label: "Projetos arquivados",
        value: this.projectsState.items.filter((project) => project.status === "archived").length,
        loading: this.projectsState.loading,
        error: this.projectsState.error,
        retry: () => this.loadProjects(),
      },
    ];
  }

  get recentSources(): KnowledgeSource[] {
    return [...this.sourcesState.items].sort(compareRecentSources).slice(0, 5);
  }

  loadSources(): void {
    this.load(this.sourcesState, this.api.sources(), "Não foi possível carregar as fontes recentes.");
  }

  loadCategories(): void {
    this.load(this.categoriesState, this.api.categories(), "Não foi possível carregar as categorias.");
  }

  loadTags(): void {
    this.load(this.tagsState, this.api.tags(), "Não foi possível carregar as tags.");
  }

  loadProjects(): void {
    this.load(this.projectsState, this.api.projects(), "Não foi possível carregar os projetos.");
  }

  formatSourceDate(source: KnowledgeSource): string {
    const date = sourceDate(source);
    return date === null ? "Data não informada" : new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(date);
  }

  search(): void {
    const query = this.searchQuery.trim();
    if (!query) return;

    this.searchStatus = "loading";
    this.searchMessage = "";
    this.api.search({ query, limit: 4 }).subscribe({
      next: (response) => {
        this.searchResults = response.results;
        this.searchStatus = "success";
        this.changeDetectorRef.markForCheck();
      },
      error: () => {
        this.searchStatus = "error";
        this.searchMessage = "Não foi possível pesquisar agora. Tente novamente em instantes.";
        this.changeDetectorRef.markForCheck();
      },
    });
  }

  resultLocation(result: KnowledgeChunk): string {
    const parts = [result.location.page ? `página ${result.location.page}` : "", result.location.section ?? ""];
    return parts.filter(Boolean).join(" · ") || "Trecho do documento";
  }

  private load<T>(state: CollectionState<T>, request: Observable<T[]>, message: string): void {
    state.loading = true;
    state.error = "";
    request.subscribe({
      next: (items) => {
        state.items = items;
        state.loading = false;
        this.changeDetectorRef.markForCheck();
      },
      error: () => {
        state.loading = false;
        state.error = message;
        this.changeDetectorRef.markForCheck();
      },
    });
  }
}

function emptyState<T>(): CollectionState<T> {
  return { items: [], loading: true, error: "" };
}

function metric<T>(label: string, state: CollectionState<T>, retry: () => void): Metric {
  return { label, value: state.items.length, loading: state.loading, error: state.error, retry };
}

export function compareRecentSources(left: KnowledgeSource, right: KnowledgeSource): number {
  const leftDate = sourceDate(left);
  const rightDate = sourceDate(right);
  if (leftDate !== null && rightDate !== null && leftDate.getTime() !== rightDate.getTime()) return rightDate.getTime() - leftDate.getTime();
  if (leftDate !== null && rightDate === null) return -1;
  if (leftDate === null && rightDate !== null) return 1;
  return left.title.localeCompare(right.title, "pt-BR") || left.source_id.localeCompare(right.source_id, "pt-BR");
}

function sourceDate(source: KnowledgeSource): Date | null {
  return parseDate(source.created_at) ?? parseDate(source.updated_at);
}

function parseDate(value: string | null): Date | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}
