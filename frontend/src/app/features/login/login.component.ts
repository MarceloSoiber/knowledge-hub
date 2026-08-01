import { CommonModule } from "@angular/common";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, Router } from "@angular/router";

import { AuthService } from "../../core/auth.service";
import { ThemeService } from "../../core/theme.service";

export function safeReturnUrl(returnUrl: string | null): string {
  return returnUrl?.startsWith("/") && !returnUrl.startsWith("//") && returnUrl !== "/login"
    ? returnUrl
    : "/inicio";
}

@Component({
  selector: "kh-login",
  imports: [CommonModule, FormsModule],
  templateUrl: "./login.component.html",
  styleUrl: "./login.component.css",
})
export class LoginComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  accessToken = "";
  rememberToken = false;

  async ngOnInit(): Promise<void> {
    await this.auth.initialize();
    if (this.auth.isAuthenticated) {
      await this.router.navigateByUrl(this.safeReturnUrl());
    }
    this.changeDetectorRef.markForCheck();
  }

  async connect(): Promise<void> {
    const authenticated = await this.auth.authenticate(this.accessToken, this.rememberToken);
    if (authenticated) {
      this.accessToken = "";
      await this.router.navigateByUrl(this.safeReturnUrl());
    }
    this.changeDetectorRef.markForCheck();
  }

  private safeReturnUrl(): string {
    return safeReturnUrl(this.route.snapshot.queryParamMap.get("returnUrl"));
  }
}
