import { HttpClient } from "@angular/common/http";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { AuthService } from "./auth.service";
import { authInterceptor } from "./auth.interceptor";

describe("authInterceptor", () => {
  let httpClient: HttpClient;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [
      provideHttpClient(withInterceptors([authInterceptor])),
      provideHttpClientTesting(),
      { provide: AuthService, useValue: { token: "test-token" } },
    ] });
    httpClient = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => { http.verify(); TestBed.resetTestingModule(); });

  it("adds Bearer only to protected Knowledge Hub requests", () => {
    httpClient.get("/api/v1/knowledge/categories").subscribe();
    const protectedRequest = http.expectOne("/api/v1/knowledge/categories");
    expect(protectedRequest.request.headers.get("Authorization")).toBe("Bearer test-token");
    protectedRequest.flush([]);

    httpClient.get("/api/v1/operations/backup").subscribe();
    const operationsRequest = http.expectOne("/api/v1/operations/backup");
    expect(operationsRequest.request.headers.get("Authorization")).toBe("Bearer test-token");
    operationsRequest.flush(new Blob());

    httpClient.get("/health").subscribe();
    const publicRequest = http.expectOne("/health");
    expect(publicRequest.request.headers.has("Authorization")).toBe(false);
    publicRequest.flush({});
  });
});
