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
});
