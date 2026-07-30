import { Component, EventEmitter, Input, Output, inject } from "@angular/core";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { Category, MetadataSelection, Project, Tag } from "../../core/knowledge.types";

@Component({
  selector: "kh-metadata-selector",
  template: `
    <fieldset [disabled]="disabled" [attr.aria-busy]="loading">
      <legend>{{ label }}</legend>
      @if (loading) { <p>Carregando metadados…</p> } @else {
        <div class="groups">
          <label><span>Categorias{{ categoriesRequired ? " (obrigatórias)" : "" }}</span><select multiple [value]="selection.categoryIds" (change)="update('categoryIds', $event)">@for (item of categories; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select></label>
          <label><span>Tags</span><input type="search" [value]="tagQuery" (input)="searchTags($event)" [disabled]="disabled" autocomplete="off" aria-label="Buscar tags" aria-controls="tag-suggestions" /><select multiple [value]="selection.tagIds" (change)="update('tagIds', $event)">@for (item of tags; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select>@if (suggestions.length) { <ul id="tag-suggestions" role="listbox" class="suggestions">@for (item of suggestions; track item.id) { <li><button type="button" (click)="addTag(item.id)">{{ item.name }}</button></li> }</ul> }</label>
          <label><span>Projetos</span><select multiple [value]="selection.projectIds" (change)="update('projectIds', $event)">@for (item of projects; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select></label>
        </div>
      }
      @if (errorMessage) { <p class="error" role="alert">{{ errorMessage }}</p> }
    </fieldset>
  `,
  styles: [`fieldset { min-width: 0; margin: 0; padding: 0; border: 0; } legend { margin-bottom: var(--space-3); color: var(--color-text); font-size: .95rem; font-weight: 800; } .groups { display: grid; gap: var(--space-4); grid-template-columns: repeat(3, minmax(0, 1fr)); } label { display: grid; gap: .5rem; color: var(--color-text); font-size: .85rem; font-weight: 750; } input, select { width: 100%; min-height: 2.7rem; padding: .55rem .65rem; border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm); outline: 0; background: var(--color-surface); color: var(--color-text); font: inherit; } input:focus, select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 12%, transparent); } select { min-height: 8.25rem; padding: .35rem; } select option { padding: .35rem .45rem; border-radius: .3rem; background: var(--color-surface); color: var(--color-text); } select option:checked { background: var(--color-primary) linear-gradient(0deg, var(--color-primary), var(--color-primary)); color: var(--color-on-primary); font-weight: 700; } .suggestions { margin: 0; padding: .3rem; list-style: none; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface); box-shadow: var(--shadow-card); } .suggestions button { width: 100%; padding: .45rem .55rem; border: 0; border-radius: .35rem; background: transparent; color: var(--color-text); text-align: left; font: inherit; cursor: pointer; } .suggestions button:hover { background: var(--color-primary-soft); } .error { color: var(--color-danger); } @media (max-width: 40rem) { .groups { grid-template-columns: 1fr; } }`],
})
export class MetadataSelectorComponent {
  private readonly api = inject(KnowledgeApiService);
  @Input() label = "Metadados";
  @Input() categories: Category[] = [];
  @Input() tags: Tag[] = [];
  @Input() projects: Project[] = [];
  @Input() selection: MetadataSelection = { categoryIds: [], tagIds: [], projectIds: [] };
  @Input() categoriesRequired = false;
  @Input() loading = false;
  @Input() disabled = false;
  @Input() errorMessage = "";
  @Output() readonly selectionChange = new EventEmitter<MetadataSelection>();
  tagQuery = "";
  suggestions: Tag[] = [];
  private searchTimer: ReturnType<typeof setTimeout> | null = null;
  private searchVersion = 0;

  update(field: keyof MetadataSelection, event: Event): void {
    const target = event.target as HTMLSelectElement;
    const ids = Array.from(target.selectedOptions, (option) => Number(option.value));
    this.selectionChange.emit({ ...this.selection, [field]: ids });
  }

  searchTags(event: Event): void {
    this.tagQuery = (event.target as HTMLInputElement).value;
    if (this.searchTimer) clearTimeout(this.searchTimer);
    const query = this.tagQuery.trim();
    const version = ++this.searchVersion;
    if (!query) { this.suggestions = []; return; }
    this.searchTimer = setTimeout(() => this.api.tagAutocomplete(query).subscribe({
      next: (items) => { if (version === this.searchVersion) this.suggestions = items.filter((item) => !this.selection.tagIds.includes(item.id)); },
      error: () => { if (version === this.searchVersion) this.suggestions = []; },
    }), 250);
  }

  addTag(id: number): void {
    if (!this.selection.tagIds.includes(id)) this.selectionChange.emit({ ...this.selection, tagIds: [...this.selection.tagIds, id] });
    this.tagQuery = ""; this.suggestions = [];
  }
}
