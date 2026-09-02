import { ComponentFixture, TestBed } from "@angular/core/testing";
import { of } from "rxjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeApiService } from "../../core/knowledge-api.service";
import { ConfigurationPageComponent } from "./configuration-page.component";

const configuration = {
  llm_provider: "local" as const,
  local_llm_base_url: "http://127.0.0.1:1234",
  local_llm_model: "gpt-oss-20b",
  api_llm_base_url: "https://api.openai.com/v1",
  api_llm_model: "gpt-4.1-mini",
  api_key_configured: false,
  embedding_model: "text-embedding-nomic-embed-text-v1.5",
  vector_dim: 768,
  origins: { local_llm_base_url: "portal" as const },
};

describe("ConfigurationPageComponent", () => {
  let fixture: ComponentFixture<ConfigurationPageComponent>;
  const api = { aiConfiguration: vi.fn(() => of(configuration)), updateAiConfiguration: vi.fn(() => of(configuration)) };

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [{ provide: KnowledgeApiService, useValue: api }] });
    fixture = TestBed.createComponent(ConfigurationPageComponent);
    fixture.detectChanges();
  });

  afterEach(() => TestBed.resetTestingModule());

  it("loads the effective configuration and exposes the protected vector dimension", () => {
    expect(api.aiConfiguration).toHaveBeenCalledOnce();
    expect(fixture.nativeElement.textContent).toContain("Dimensão protegida");
    expect(fixture.nativeElement.querySelector('[name="vectorDim"]')?.disabled).toBe(true);
  });

  it("saves the selected provider and does not send a blank API key", () => {
    fixture.componentInstance.save();

    expect(api.updateAiConfiguration).toHaveBeenCalledWith(expect.objectContaining({
      llm_provider: "local", local_llm_model: "gpt-oss-20b", vector_dim: 768,
    }));
    expect(api.updateAiConfiguration.mock.calls[0][0].api_key).toBeUndefined();
  });
});
