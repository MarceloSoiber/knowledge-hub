import { TestBed } from "@angular/core/testing";
import { Router } from "@angular/router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthService } from "./auth.service";
import { authGuard } from "./auth.guard";

describe("authGuard", () => {
  afterEach(() => TestBed.resetTestingModule());

  it("allows authenticated sessions after initialization", async () => {
    const auth = { initialize: vi.fn(async () => undefined), isAuthenticated: true };
    TestBed.configureTestingModule({ providers: [{ provide: AuthService, useValue: auth }, { provide: Router, useValue: {} }] });

    await expect(TestBed.runInInjectionContext(() => authGuard({} as never, { url: "/biblioteca" } as never))).resolves.toBe(true);
    expect(auth.initialize).toHaveBeenCalledOnce();
  });

  it("redirects unauthenticated sessions to login with the intended local route", async () => {
    const tree = {};
    const router = { createUrlTree: vi.fn(() => tree) };
    TestBed.configureTestingModule({ providers: [{ provide: AuthService, useValue: { initialize: async () => undefined, isAuthenticated: false } }, { provide: Router, useValue: router }] });

    await expect(TestBed.runInInjectionContext(() => authGuard({} as never, { url: "/busca" } as never))).resolves.toBe(tree);
    expect(router.createUrlTree).toHaveBeenCalledWith(["/login"], { queryParams: { returnUrl: "/busca" } });
  });
});
