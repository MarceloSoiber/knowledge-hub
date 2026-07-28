import { TestBed } from "@angular/core/testing";
import { afterEach, describe, expect, it } from "vitest";

import { ThemeService } from "./theme.service";

describe("ThemeService", () => {
  afterEach(() => {
    localStorage.removeItem("knowledge-hub.theme");
    delete document.documentElement.dataset["theme"];
    document.documentElement.style.colorScheme = "";
    TestBed.resetTestingModule();
  });

  it("persists a user choice and exposes it on the document", () => {
    const theme = TestBed.inject(ThemeService);

    theme.setTheme("dark");

    expect(theme.current()).toBe("dark");
    expect(document.documentElement.dataset["theme"]).toBe("dark");
    expect(localStorage.getItem("knowledge-hub.theme")).toBe("dark");
  });

  it("toggles between light and dark themes", () => {
    const theme = TestBed.inject(ThemeService);
    theme.setTheme("light");

    theme.toggle();

    expect(theme.current()).toBe("dark");
  });
});
