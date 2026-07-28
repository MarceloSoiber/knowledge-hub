import { HttpClient } from "@angular/common/http";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { Router } from "@angular/router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthService } from "./auth.service";
import { unauthorizedInterceptor } from "./unauthorized.interceptor";

describe("unauthorizedInterceptor", () => {
  let httpClient: HttpClient;
  let http: HttpTestingController;
  let auth: { logout: ReturnType<typeof vi.fn> };
  let router: { url: string; navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    auth = { logout: vi.fn() };
    router = { url: "/biblioteca", navigate: vi.fn(() => Promise.resolve(true)) };
    TestBed.configureTestingModule({ providers: [
      provideHttpClient(withInterceptors([unauthorizedInterceptor])),
      provideHttpClientTesting(),
      { provide: AuthService, useValue: auth },
      { provide: Router, useValue: router },
    ] });
    httpClient = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => { http.verify(); TestBed.resetTestingModule(); });

  it("clears session and navigates after a protected 401", () => {
    httpClient.get("/api/v1/knowledge/sources").subscribe({ error: () => undefined });
    http.expectOne("/api/v1/knowledge/sources").flush({}, { status: 401, statusText: "Unauthorized" });

    expect(auth.logout).toHaveBeenCalledOnce();
    expect(router.navigate).toHaveBeenCalledWith(["/login"]);
  });

  it("does not clear a session for a 401 outside the protected prefix", () => {
    httpClient.get("/health").subscribe({ error: () => undefined });
    http.expectOne("/health").flush({}, { status: 401, statusText: "Unauthorized" });

    expect(auth.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });
});
