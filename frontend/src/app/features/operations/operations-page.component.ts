import { Component, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { KnowledgeApiService } from "../../core/knowledge-api.service";

@Component({ selector: "kh-operations-page", imports: [FormsModule], templateUrl: "./operations-page.component.html", styleUrl: "./operations-page.component.css" })
export class OperationsPageComponent {
  private readonly api = inject(KnowledgeApiService);
  file: File | null = null; confirmation = ""; status = "idle"; message = "";
  download(): void { this.status = "backup"; this.api.backup().subscribe({ next: (blob) => { const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "knowledge-hub-backup.dump"; anchor.click(); URL.revokeObjectURL(url); this.status = "idle"; }, error: () => { this.status = "idle"; this.message = "Não foi possível gerar o backup."; } }); }
  choose(event: Event): void { this.file = (event.target as HTMLInputElement).files?.item(0) ?? null; }
  restore(): void { if (!this.file || this.confirmation !== "RESTAURAR BASE") return; this.status = "restore"; this.message = ""; this.api.restoreBackup(this.file, this.confirmation).subscribe({ next: (result) => { this.status = "done"; this.message = `${result.message} Backup de segurança: ${result.safety_backup}.`; }, error: (error) => { this.status = "idle"; this.message = error.error?.detail ?? "Não foi possível restaurar o backup."; } }); }
}
