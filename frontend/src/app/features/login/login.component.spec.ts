import { describe, expect, it } from "vitest";

import { safeReturnUrl } from "./login.component";

describe("safeReturnUrl", () => {
  it("keeps valid private routes", () => {
    expect(safeReturnUrl("/biblioteca?from=dashboard")).toBe("/biblioteca?from=dashboard");
  });

  it("rejects open redirects and the login route", () => {
    expect(safeReturnUrl("//outside.example")).toBe("/inicio");
    expect(safeReturnUrl("https://outside.example")).toBe("/inicio");
    expect(safeReturnUrl("/login")).toBe("/inicio");
    expect(safeReturnUrl(null)).toBe("/inicio");
  });
});
