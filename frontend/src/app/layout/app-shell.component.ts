import { Component, inject } from "@angular/core";
import { Router, RouterLink, RouterOutlet } from "@angular/router";

import { AuthService } from "../core/auth.service";

@Component({
  selector: "kh-app-shell",
  imports: [RouterLink, RouterOutlet],
  templateUrl: "./app-shell.component.html",
  styleUrl: "./app-shell.component.css",
})
export class AppShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  async logout(): Promise<void> {
    this.auth.logout();
    await this.router.navigateByUrl("/login");
  }
}
