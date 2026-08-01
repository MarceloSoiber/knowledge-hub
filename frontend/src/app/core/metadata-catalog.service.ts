import { Injectable, computed, signal } from "@angular/core";
import { forkJoin } from "rxjs";

import { KnowledgeApiService } from "./knowledge-api.service";
import { Category, Project, Tag } from "./knowledge.types";

@Injectable({ providedIn: "root" })
export class MetadataCatalogService {
  readonly categories = signal<Category[]>([]);
  readonly tags = signal<Tag[]>([]);
  readonly projects = signal<Project[]>([]);
  readonly loading = signal(false);
  readonly error = signal("");
  readonly activeProjects = computed(() => this.projects().filter((project) => project.status === "active"));

  constructor(private readonly api: KnowledgeApiService) {}

  load(force = false): void {
    if (this.loading() || (!force && (this.categories().length || this.tags().length || this.projects().length))) return;
    this.loading.set(true); this.error.set("");
    forkJoin({ categories: this.api.categories(), tags: this.api.tags(), projects: this.api.projects() }).subscribe({
      next: (data) => { this.categories.set(sortByName(data.categories)); this.tags.set(sortByName(data.tags)); this.projects.set(sortByName(data.projects)); this.loading.set(false); },
      error: () => { this.error.set("Não foi possível carregar os metadados. Tente novamente."); this.loading.set(false); },
    });
  }

  upsertCategory(item: Category): void { this.categories.set(upsert(this.categories(), item)); }
  removeCategory(id: number): void { this.categories.set(this.categories().filter((item) => item.id !== id)); }
  upsertTag(item: Tag): void { this.tags.set(upsert(this.tags(), item)); }
  removeTag(id: number): void { this.tags.set(this.tags().filter((item) => item.id !== id)); }
  upsertProject(item: Project): void { this.projects.set(upsert(this.projects(), item)); }
}

function upsert<T extends { id: number; name: string }>(items: T[], item: T): T[] {
  return sortByName([...items.filter((current) => current.id !== item.id), item]);
}
function sortByName<T extends { name: string }>(items: T[]): T[] { return [...items].sort((a, b) => a.name.localeCompare(b.name, "pt-BR")); }
