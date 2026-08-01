import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { RouterLink, ActivatedRoute } from "@angular/router";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { KnowledgeSourceDetail } from "../../shared/models/knowledge.models";

@Component({
  selector: "kh-source-detail",
  imports: [RouterLink],
  templateUrl: "./source-detail.component.html",
  styleUrl: "./source-detail.component.css",
})
export class SourceDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(KnowledgeApiService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);

  source: KnowledgeSourceDetail | null = null;
  loading = true;
  message = "";

  ngOnInit(): void {
    const sourceId = this.route.snapshot.paramMap.get("sourceId");
    if (!sourceId) {
      this.loading = false;
      this.message = "A fonte solicitada não é válida.";
      return;
    }
    this.api.source(sourceId).subscribe({
      next: (source) => {
        this.source = source;
        this.loading = false;
        this.changeDetectorRef.markForCheck();
      },
      error: (error: HttpErrorResponse) => {
        this.loading = false;
        this.message = error.status === 404 ? "Esta fonte não existe mais." : "Não foi possível carregar a fonte.";
        this.changeDetectorRef.markForCheck();
      },
    });
  }
}
