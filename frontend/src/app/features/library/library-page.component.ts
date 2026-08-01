import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { Category, KnowledgeSource, Project, Tag } from "../../core/knowledge.types";
import { EmptyStateComponent } from "../../shared/empty-state/empty-state.component";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";

@Component({
  selector: "kh-library-page",
  imports: [FormsModule, RouterLink, LoadingStateComponent, ErrorStateComponent, EmptyStateComponent],
  templateUrl: "./library-page.component.html",
  styleUrl: "./library-page.component.css",
})
export class LibraryPageComponent implements OnInit {
  private readonly api = inject(KnowledgeApiService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  sources: KnowledgeSource[] = [];
  query = "";
  categoryIds: number[] = [];
  tagIds: number[] = [];
  projectIds: number[] = [];
  loading = true;
  error = "";

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading = true;
    this.error = "";
    this.api.sources().subscribe({
      next: (sources) => { this.sources = sources; this.loading = false; this.changeDetectorRef.markForCheck(); },
      error: () => { this.loading = false; this.error = "Não foi possível carregar o acervo. Tente novamente."; this.changeDetectorRef.markForCheck(); },
    });
  }

  get categories(): Category[] { return uniqueById(this.sources.flatMap((source) => source.categories)); }
  get tags(): Tag[] { return uniqueById(this.sources.flatMap((source) => source.tags)); }
  get projects(): Project[] { return uniqueById(this.sources.flatMap((source) => source.projects)); }
  get filteredSources(): KnowledgeSource[] {
    const query = normalized(this.query);
    return this.sources.filter((source) =>
      (!query || normalized(source.title).includes(query))
      && containsAll(source.categories, this.categoryIds)
      && containsAll(source.tags, this.tagIds)
      && containsAll(source.projects, this.projectIds));
  }
  get hasFilters(): boolean { return Boolean(this.query || this.categoryIds.length || this.tagIds.length || this.projectIds.length); }

  selectedIds(event: Event): number[] {
    const select = event.target as HTMLSelectElement;
    return Array.from(select.selectedOptions, (option) => Number(option.value)).filter((id) => Number.isInteger(id) && id > 0);
  }
  clearFilters(): void { this.query = ""; this.categoryIds = []; this.tagIds = []; this.projectIds = []; }
}

function normalized(value: string): string { return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase(); }
function containsAll(items: Array<{ id: number }>, ids: number[]): boolean { return ids.every((id) => items.some((item) => item.id === id)); }
function uniqueById<T extends { id: number }>(items: T[]): T[] { return Array.from(new Map(items.map((item) => [item.id, item])).values()); }
