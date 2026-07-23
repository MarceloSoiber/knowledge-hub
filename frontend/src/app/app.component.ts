import { CommonModule } from "@angular/common";
import { ChangeDetectorRef, Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";

import { AuthService } from "./core/auth.service";

@Component({
  selector: "kh-root",
  imports: [CommonModule, FormsModule],
  templateUrl: "./app.component.html",
  styleUrl: "./app.component.css",
})
export class AppComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly changeDetectorRef = inject(ChangeDetectorRef);
  accessToken = "";
  rememberToken = false;

  async ngOnInit(): Promise<void> {
    await this.auth.initialize();
    this.changeDetectorRef.markForCheck();
  }

  async connect(): Promise<void> {
    await this.auth.authenticate(this.accessToken, this.rememberToken);
    if (this.auth.status === "authenticated") {
      this.accessToken = "";
    }
    this.changeDetectorRef.markForCheck();
  }

  disconnect(): void {
    this.accessToken = "";
    this.rememberToken = false;
    this.auth.logout();
  }
}
