import { ComponentFixture, TestBed } from "@angular/core/testing";
import { provideRouter } from "@angular/router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthService } from "../core/auth.service";
import { AuthenticatedLayoutComponent } from "./authenticated-layout.component";

describe("AuthenticatedLayoutComponent", () => {
  let fixture: ComponentFixture<AuthenticatedLayoutComponent>;
  const auth = { logout: vi.fn() };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    });
    fixture = TestBed.createComponent(AuthenticatedLayoutComponent);
    fixture.detectChanges();
  });

  afterEach(() => TestBed.resetTestingModule());

  it("exposes a skip link and every private destination", () => {
    const links = Array.from(fixture.nativeElement.querySelectorAll("a"), (link: HTMLAnchorElement) => link.textContent?.trim());
    for (const label of ["Pular para o conteúdo", "Início", "Busca inteligente", "Pergunte à base", "Ingestão", "Biblioteca", "Organização"]) {
      expect(links.some((text) => text?.includes(label))).toBe(true);
    }
    expect(fixture.nativeElement.querySelector(".skip-link")?.getAttribute("href")).toBe("#main-content");
  });

  it("closes the mobile menu with Escape and returns focus to its trigger", () => {
    const button = fixture.nativeElement.querySelector(".menu-button") as HTMLButtonElement;
    button.focus();
    button.click();
    expect(fixture.componentInstance.menuOpen).toBe(true);

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));

    expect(fixture.componentInstance.menuOpen).toBe(false);
    expect(document.activeElement).toBe(button);
  });

  it("closes the mobile menu when the backdrop is activated", () => {
    fixture.componentInstance.menuOpen = true;
    fixture.detectChanges();
    (fixture.nativeElement.querySelector(".backdrop") as HTMLButtonElement).click();
    expect(fixture.componentInstance.menuOpen).toBe(false);
  });

  it("shows a button to return to the top after a long scroll", () => {
    fixture.componentInstance.showBackToTop = true;
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector(".back-to-top")?.textContent).toContain("Topo");
  });
});
