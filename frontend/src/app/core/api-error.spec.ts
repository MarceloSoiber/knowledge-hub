import { HttpErrorResponse } from "@angular/common/http";
import { describe, expect, it } from "vitest";

import { toApiError } from "./api-error";

describe("toApiError", () => {
  it("normalizes connection failures without exposing the response payload", () => {
    const error = toApiError(new HttpErrorResponse({ status: 0, error: "untrusted detail" }));

    expect(error).toEqual({
      kind: "network",
      status: 0,
      message: "Não foi possível conectar à API. Confira a conexão.",
    });
  });

  it("classifies unauthorized responses for the session flow", () => {
    expect(toApiError(new HttpErrorResponse({ status: 401 })).kind).toBe("unauthorized");
  });

  it.each([
    [400, "validation"], [403, "forbidden"], [404, "not-found"], [409, "conflict"], [413, "too-large"],
    [429, "rate-limited"], [502, "provider"], [503, "unavailable"],
  ] as const)("maps status %i to a safe %s error", (status, kind) => {
    const error = toApiError(new HttpErrorResponse({ status, error: "<script>untrusted</script>" }));
    expect(error.kind).toBe(kind);
    expect(error.message).not.toContain("untrusted");
    expect(error.message).not.toContain("<script>");
  });

  it("uses a safe fallback for unmapped errors", () => {
    const error = toApiError(new HttpErrorResponse({ status: 500, error: { detail: "token-secret" } }));
    expect(error.kind).toBe("unknown");
    expect(error.message).not.toContain("token-secret");
  });
});
