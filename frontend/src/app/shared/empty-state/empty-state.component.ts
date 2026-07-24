import { Component, Input } from "@angular/core";

@Component({
  selector: "kh-empty-state",
  template: `<section class="empty"><h2>{{ title }}</h2><p>{{ description }}</p><ng-content /></section>`,
  styles: [`.empty { padding: clamp(1.25rem, 5vw, 2rem); border: 1px dashed var(--color-border-strong); border-radius: var(--radius-md); background: var(--color-surface); } h2 { margin: 0; font-size: 1.15rem; } p { margin: var(--space-2) 0 0; color: var(--color-muted); }`],
})
export class EmptyStateComponent {
  @Input({ required: true }) title = "";
  @Input({ required: true }) description = "";
}
