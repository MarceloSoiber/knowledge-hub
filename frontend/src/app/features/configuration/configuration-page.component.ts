import { Component, inject } from "@angular/core";
import { HttpErrorResponse } from "@angular/common/http";
import { FormsModule } from "@angular/forms";

import { toApiError } from "../../core/api-error";
import { AIConfiguration, AIConfigurationWrite, LLMProvider } from "../../core/knowledge.types";
import { KnowledgeApiService } from "../../core/knowledge-api.service";

@Component({
  selector: "kh-configuration-page",
  imports: [FormsModule],
  templateUrl: "./configuration-page.component.html",
  styleUrl: "./configuration-page.component.css",
})
export class ConfigurationPageComponent {
  private readonly api = inject(KnowledgeApiService);
  configuration: AIConfiguration | null = null;
  provider: LLMProvider = "local";
  localBaseUrl = ""; localModel = ""; apiBaseUrl = ""; apiModel = ""; apiKey = ""; embeddingModel = ""; vectorDim = 768;
  status: "loading" | "idle" | "saving" | "error" | "success" = "loading";
  message = "";

  constructor() { this.load(); }

  load(): void {
    this.status = "loading"; this.message = "";
    this.api.aiConfiguration().subscribe({
      next: (configuration) => { this.apply(configuration); this.status = "idle"; },
      error: (error: HttpErrorResponse) => { this.status = "error"; this.message = toApiError(error).message; },
    });
  }

  save(): void {
    if (!this.localBaseUrl.trim() || !this.localModel.trim() || !this.apiBaseUrl.trim() || !this.apiModel.trim() || !this.embeddingModel.trim()) {
      this.status = "error"; this.message = "Preencha todos os endpoints e modelos antes de salvar."; return;
    }
    const payload: AIConfigurationWrite = {
      llm_provider: this.provider,
      local_llm_base_url: this.localBaseUrl.trim(), local_llm_model: this.localModel.trim(),
      api_llm_base_url: this.apiBaseUrl.trim(), api_llm_model: this.apiModel.trim(),
      embedding_model: this.embeddingModel.trim(), vector_dim: this.vectorDim,
    };
    if (this.apiKey.trim()) payload.api_key = this.apiKey.trim();
    this.status = "saving"; this.message = "";
    this.api.updateAiConfiguration(payload).subscribe({
      next: (configuration) => { this.apply(configuration); this.apiKey = ""; this.status = "success"; this.message = "Configuração de IA salva. Novas requisições usarão os valores ativos."; },
      error: (error: HttpErrorResponse) => { this.status = "error"; this.message = error.error?.detail ?? toApiError(error).message; },
    });
  }

  origin(key: string): string { return this.configuration?.origins?.[key] === "portal" ? "Portal" : "Ambiente"; }
  get isApiProvider(): boolean { return this.provider === "api"; }

  private apply(configuration: AIConfiguration): void {
    this.configuration = { ...configuration, origins: configuration.origins ?? {} };
    this.provider = configuration.llm_provider === "api" ? "api" : "local";
    this.localBaseUrl = configuration.local_llm_base_url || "http://127.0.0.1:1234";
    this.localModel = configuration.local_llm_model || "gemma-4-12b-it";
    this.apiBaseUrl = configuration.api_llm_base_url || "https://api.openai.com/v1";
    this.apiModel = configuration.api_llm_model || "gpt-4.1-mini";
    this.embeddingModel = configuration.embedding_model || "text-embedding-nomic-embed-text-v1.5";
    this.vectorDim = configuration.vector_dim || 768;
  }
}
