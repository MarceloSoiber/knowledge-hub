import { Component, ElementRef, HostListener, ViewChild, inject } from "@angular/core";
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";

import { AuthService } from "../core/auth.service";
import { ThemeService } from "../core/theme.service";

@Component({
  selector: "kh-authenticated-layout",
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: "./authenticated-layout.component.html",
  styleUrl: "./authenticated-layout.component.css",
})
export class AuthenticatedLayoutComponent {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly router = inject(Router);
  @ViewChild("menuButton") private readonly menuButton?: ElementRef<HTMLButtonElement>;
  menuOpen = false;

  async logout(): Promise<void> {
    this.auth.logout();
    await this.router.navigate(["/login"]);
  }

  closeMenu(returnFocus = false): void {
    if (!this.menuOpen) return;
    this.menuOpen = false;
    if (returnFocus) this.menuButton?.nativeElement.focus();
  }

  @HostListener("document:keydown.escape")
  onEscape(): void { this.closeMenu(true); }
}
