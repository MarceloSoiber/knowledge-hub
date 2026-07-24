import { CommonModule } from "@angular/common";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, Router } from "@angular/router";

import { AuthService } from "../../core/auth.service";

@Component({
  selector: "kh-login",
  imports: [CommonModule, FormsModule],
  templateUrl: "./login.component.html",
  styleUrl: "./login.component.css",
})
export class LoginComponent implements OnInit {
  readonly auth = inject(AuthService);
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
    const returnUrl = this.route.snapshot.queryParamMap.get("returnUrl");
    return returnUrl?.startsWith("/") && !returnUrl.startsWith("//") && returnUrl !== "/login"
      ? returnUrl
      : "/inicio";
  }
}
