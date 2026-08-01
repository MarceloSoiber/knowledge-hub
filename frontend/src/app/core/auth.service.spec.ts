import { TestBed } from "@angular/core/testing";
import { of, throwError } from "rxjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeApiService } from "./knowledge-api.service";
import { AuthService } from "./auth.service";

describe("AuthService", () => {
  const storageKey = "knowledge-hub.auth-token";
  let categories: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorage.clear();
    categories = vi.fn(() => of([]));
    TestBed.configureTestingModule({ providers: [{ provide: KnowledgeApiService, useValue: { categories } }] });
  });

  afterEach(() => {
    localStorage.clear();
    TestBed.resetTestingModule();
  });

  it("rejects blank tokens without calling the API", async () => {
    const service = TestBed.inject(AuthService);

    await expect(service.authenticate("   ", false)).resolves.toBe(false);
    expect(categories).not.toHaveBeenCalled();
    expect(service.errorMessage).toContain("Informe o token");
  });

  it("keeps a validated token only when the user chooses to remember it", async () => {
    const service = TestBed.inject(AuthService);
    await expect(service.authenticate("token-de-teste", false)).resolves.toBe(true);
    expect(service.isAuthenticated).toBe(true);
    expect(localStorage.getItem(storageKey)).toBeNull();

    service.logout();
    await expect(service.authenticate("outro-token", true)).resolves.toBe(true);
    expect(localStorage.getItem(storageKey)).toBe("outro-token");
  });

  it("clears a failed persisted session without exposing the token", async () => {
    localStorage.setItem(storageKey, "token-secreto");
    categories.mockReturnValueOnce(throwError(() => new Error("offline")));
    const service = TestBed.inject(AuthService);

    await service.initialize();
    expect(service.isAuthenticated).toBe(false);
    expect(service.status).toBe("error");
    expect(service.errorMessage).not.toContain("token-secreto");
    expect(localStorage.getItem(storageKey)).toBeNull();
  });
});
