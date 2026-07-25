import { Component } from "@angular/core";

import { EmptyStateComponent } from "../../shared/empty-state/empty-state.component";

@Component({
  selector: "kh-home",
  imports: [EmptyStateComponent],
  template: `
    <section class="home" aria-labelledby="home-title">
      <p class="eyebrow">Área autenticada</p>
      <h1 id="home-title">Seu acervo está pronto para começar.</h1>
      <kh-empty-state title="Próximas ações em breve" description="Busca, ingestão e organização serão adicionadas nas próximas entregas." />
    </section>
  `,
  styles: [`.home { max-width: 48rem; } h1 { margin: 0 0 var(--space-6); font-size: clamp(1.8rem, 5vw, 2.6rem); letter-spacing: -.04em; } .eyebrow { margin: 0 0 var(--space-2); color: var(--color-primary); font-weight: 700; }`],
})
export class HomeComponent {}
