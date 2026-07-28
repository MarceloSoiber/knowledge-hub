import { DOCUMENT } from "@angular/common";
import { Injectable, inject, signal } from "@angular/core";

export type Theme = "light" | "dark";

const storageKey = "knowledge-hub.theme";

@Injectable({ providedIn: "root" })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  readonly current = signal<Theme>(this.readInitialTheme());

  constructor() {
    this.apply(this.current());
  }

  toggle(): void {
    this.setTheme(this.current() === "dark" ? "light" : "dark");
  }

  setTheme(theme: Theme): void {
    this.current.set(theme);
    this.apply(theme);
    if (typeof localStorage !== "undefined") localStorage.setItem(storageKey, theme);
  }

  private readInitialTheme(): Theme {
    const stored = typeof localStorage === "undefined" ? null : localStorage.getItem(storageKey);
    if (stored === "light" || stored === "dark") return stored;
    return typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  private apply(theme: Theme): void {
    this.document.documentElement.dataset["theme"] = theme;
    this.document.documentElement.style.colorScheme = theme;
  }
}
