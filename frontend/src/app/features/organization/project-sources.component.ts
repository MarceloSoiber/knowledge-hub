import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { ActivatedRoute, RouterLink } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { KnowledgeSource } from "../../core/knowledge.types";
import { EmptyStateComponent } from "../../shared/empty-state/empty-state.component";
import { ErrorStateComponent } from "../../shared/error-state/error-state.component";
import { LoadingStateComponent } from "../../shared/loading-state/loading-state.component";

@Component({
  selector: "kh-project-sources",
  imports: [RouterLink, EmptyStateComponent, ErrorStateComponent, LoadingStateComponent],
  template: `<section aria-labelledby="project-sources-title"><a routerLink="/organizacao">← Voltar à Organização</a><h1 id="project-sources-title">Fontes do projeto</h1>@if (loading) { <kh-loading-state message="Carregando fontes do projeto…" /> } @else if (error) { <kh-error-state title="Fontes indisponíveis" [message]="error" [showRetry]="true" (retry)="load()" /> } @else if (!sources.length) { <kh-empty-state title="Nenhuma fonte vinculada" description="Este projeto ainda não possui fontes." /> } @else { <ul class="sources">@for (source of sources; track source.source_id) { <li><a [routerLink]="['/sources', source.source_id]">{{ source.title }}</a><span>{{ source.source_type }} · {{ source.uri }}</span><small>@for (category of source.categories; track category.id) { {{ category.name }} } @for (tag of source.tags; track tag.id) { #{{ tag.name }} } @for (project of source.projects; track project.id) { {{ project.name }} }</small></li> }</ul> }</section>`,
  styles: [`.sources { display: grid; gap: var(--space-3); padding: 0; list-style: none; } .sources li { display: grid; gap: .35rem; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-sm); } span, small { color: var(--color-muted); }`],
})
export class ProjectSourcesComponent implements OnInit {
  private readonly api = inject(KnowledgeApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);
  sources: KnowledgeSource[] = [];
  loading = true;
  error = "";
  private projectId = 0;
  ngOnInit(): void { this.projectId = Number(this.route.snapshot.paramMap.get("projectId")); this.load(); }
  load(): void {
    if (!Number.isInteger(this.projectId) || this.projectId <= 0) { this.loading = false; this.error = "O projeto solicitado não é válido."; return; }
    this.loading = true; this.error = "";
    this.api.projectSources(this.projectId).subscribe({ next: (sources) => { this.sources = sources; this.loading = false; this.cdr.markForCheck(); }, error: (error) => { this.loading = false; this.error = error.status === 404 ? "Este projeto não existe mais." : "Não foi possível carregar as fontes do projeto."; this.cdr.markForCheck(); } });
  }
}
