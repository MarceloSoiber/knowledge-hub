import { ChangeDetectorRef, Component, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Router } from "@angular/router";

import { AuthService } from "../../core/auth.service";

@Component({
  selector: "kh-login",
  imports: [FormsModule],
  templateUrl: "./login.component.html",
  styleUrl: "./login.component.css",
})
export class LoginComponent {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);

  accessToken = "";
  rememberToken = this.auth.rememberToken;

  async connect(): Promise<void> {
    const authenticated = await this.auth.authenticate(this.accessToken, this.rememberToken);
    this.changeDetectorRef.markForCheck();
    if (authenticated) {
      this.accessToken = "";
      await this.router.navigateByUrl("/search");
    }
  }
}
