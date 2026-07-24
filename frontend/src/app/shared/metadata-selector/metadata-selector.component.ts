import { Component, EventEmitter, Input, Output } from "@angular/core";

import { Category, MetadataSelection, Project, Tag } from "../../core/knowledge.types";

@Component({
  selector: "kh-metadata-selector",
  template: `
    <fieldset [disabled]="disabled" [attr.aria-busy]="loading">
      <legend>{{ label }}</legend>
      @if (loading) { <p>Carregando metadados…</p> } @else {
        <div class="groups">
          <label><span>Categorias{{ categoriesRequired ? " (obrigatórias)" : "" }}</span><select multiple [value]="selection.categoryIds" (change)="update('categoryIds', $event)">@for (item of categories; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select></label>
          <label><span>Tags</span><select multiple [value]="selection.tagIds" (change)="update('tagIds', $event)">@for (item of tags; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select></label>
          <label><span>Projetos</span><select multiple [value]="selection.projectIds" (change)="update('projectIds', $event)">@for (item of projects; track item.id) { <option [value]="item.id">{{ item.name }}</option> }</select></label>
        </div>
      }
      @if (errorMessage) { <p class="error" role="alert">{{ errorMessage }}</p> }
    </fieldset>
  `,
  styles: [`.groups { display: grid; gap: var(--space-4); grid-template-columns: repeat(3, minmax(0, 1fr)); } label { display: grid; gap: .4rem; color: var(--color-text); font-weight: 650; } select { min-height: 7rem; padding: .4rem; border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm); background: var(--color-surface); } .error { color: var(--color-danger); } @media (max-width: 40rem) { .groups { grid-template-columns: 1fr; } }`],
})
export class MetadataSelectorComponent {
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

  update(field: keyof MetadataSelection, event: Event): void {
    const target = event.target as HTMLSelectElement;
    const ids = Array.from(target.selectedOptions, (option) => Number(option.value));
    this.selectionChange.emit({ ...this.selection, [field]: ids });
  }
}
