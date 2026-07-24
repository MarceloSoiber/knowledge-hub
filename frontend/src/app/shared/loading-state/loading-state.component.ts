import { Component, Input } from "@angular/core";

@Component({
  selector: "kh-loading-state",
  template: `<div class="loading" role="status" aria-live="polite" aria-busy="true"><span class="spinner" aria-hidden="true"></span><span>{{ message }}</span></div>`,
  styles: [`.loading { display: flex; align-items: center; gap: .7rem; color: var(--color-muted); } .spinner { width: 1.2rem; height: 1.2rem; border: 2px solid var(--color-border-strong); border-top-color: var(--color-primary); border-radius: 50%; animation: spin .8s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } } @media (prefers-reduced-motion: reduce) { .spinner { animation: none; border-top-color: var(--color-border-strong); } }`],
})
export class LoadingStateComponent { @Input() message = "Carregando…"; }
