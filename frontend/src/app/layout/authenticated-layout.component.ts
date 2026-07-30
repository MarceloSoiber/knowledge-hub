import { Component, ElementRef, HostListener, ViewChild, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";

import { AuthService } from "../core/auth.service";
import { ThemeService } from "../core/theme.service";
import { KnowledgeApiService } from "../core/knowledge-api.service";
import { KnowledgeChunk } from "../core/knowledge.types";

@Component({
  selector: "kh-authenticated-layout",
  imports: [FormsModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: "./authenticated-layout.component.html",
  styleUrl: "./authenticated-layout.component.css",
})
export class AuthenticatedLayoutComponent {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly api = inject(KnowledgeApiService);
  private readonly router = inject(Router);
  @ViewChild("menuButton") private readonly menuButton?: ElementRef<HTMLButtonElement>;
  @ViewChild("globalSearchInput") private readonly globalSearchInput?: ElementRef<HTMLInputElement>;
  menuOpen = false;
  showBackToTop = false;
  globalQuery = "";
  globalResults: KnowledgeChunk[] = [];
  globalSearchStatus: "idle" | "loading" | "error" = "idle";

  async logout(): Promise<void> {
    this.auth.logout();
    await this.router.navigate(["/login"]);
  }

  closeMenu(returnFocus = false): void {
    if (!this.menuOpen) return;
    this.menuOpen = false;
    if (returnFocus) this.menuButton?.nativeElement.focus();
  }

  searchGlobal(): void {
    const query = this.globalQuery.trim();
    if (!query) return;
    this.globalSearchStatus = "loading";
    this.globalResults = [];
    this.api.search({ query, limit: 4 }).subscribe({
      next: (response) => { this.globalResults = response.results; this.globalSearchStatus = "idle"; },
      error: () => { this.globalSearchStatus = "error"; },
    });
  }

  closeGlobalSearch(): void { this.globalResults = []; this.globalSearchStatus = "idle"; }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  @HostListener("document:keydown.escape")
  onEscape(): void { this.closeMenu(true); this.closeGlobalSearch(); }

  @HostListener("window:scroll")
  onScroll(): void { this.showBackToTop = window.scrollY > 480; }

  @HostListener("document:keydown", ["$event"])
  onShortcut(event: KeyboardEvent): void {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); this.globalSearchInput?.nativeElement.focus(); }
  }
}
