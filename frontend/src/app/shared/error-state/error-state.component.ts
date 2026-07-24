import { Component, EventEmitter, Input, Output } from "@angular/core";

@Component({
  selector: "kh-error-state",
  template: `<section class="error" role="alert"><h2>{{ title }}</h2><p>{{ message }}</p>@if (showRetry) { <button type="button" (click)="retry.emit()">Tentar novamente</button> }</section>`,
  styles: [`.error { padding: var(--space-4); border: 1px solid #efb7b7; border-radius: var(--radius-sm); background: var(--color-danger-soft); color: var(--color-danger); } h2, p { margin: 0; } p { margin-top: var(--space-2); } button { margin-top: var(--space-3); border: 0; border-radius: var(--radius-sm); padding: .55rem .7rem; background: var(--color-danger); color: #fff; font: inherit; font-weight: 650; cursor: pointer; }`],
})
export class ErrorStateComponent {
  @Input() title = "Não foi possível concluir esta ação";
  @Input() message = "Tente novamente em alguns instantes.";
  @Input() showRetry = false;
  @Output() readonly retry = new EventEmitter<void>();
}
