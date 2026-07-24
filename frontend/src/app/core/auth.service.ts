import { Injectable, inject } from "@angular/core";
import { firstValueFrom } from "rxjs";

import { KnowledgeApiService } from "./knowledge-api.service";

export type AuthStatus = "checking" | "unauthenticated" | "authenticated" | "error";

@Injectable({ providedIn: "root" })
export class AuthService {
  private readonly api = inject(KnowledgeApiService);
  private readonly storageKey = "knowledge-hub.auth-token";
  private initialization: Promise<void> | null = null;

  token: string | null = null;
  status: AuthStatus = "checking";
  errorMessage = "";
  rememberToken = false;

  get isAuthenticated(): boolean { return this.status === "authenticated" && this.token !== null; }

  async initialize(): Promise<void> {
    if (this.initialization) return this.initialization;
    this.initialization = this.restoreSession();
    return this.initialization;
  }

  private async restoreSession(): Promise<void> {
    const storedToken = localStorage.getItem(this.storageKey);
    if (!storedToken) {
      this.status = "unauthenticated";
      return;
    }

    this.rememberToken = true;
    await this.authenticate(storedToken, true);
  }

  async authenticate(token: string, remember: boolean): Promise<boolean> {
    const normalizedToken = token.trim();
    if (!normalizedToken) {
      this.errorMessage = "Informe o token de acesso.";
      this.status = "error";
      return false;
    }

    this.token = normalizedToken;
    this.rememberToken = remember;
    this.status = "checking";
    this.errorMessage = "";

    try {
      await firstValueFrom(this.api.categories());
      if (remember) {
        localStorage.setItem(this.storageKey, normalizedToken);
      } else {
        localStorage.removeItem(this.storageKey);
      }
      this.status = "authenticated";
      return true;
    } catch {
      this.clearSession();
      this.errorMessage = "Token inválido ou API indisponível. Confira a conexão e tente novamente.";
      this.status = "error";
      return false;
    }
  }

  logout(): void {
    this.clearSession();
    this.status = "unauthenticated";
    this.errorMessage = "";
  }

  private clearSession(): void {
    this.token = null;
    this.rememberToken = false;
    localStorage.removeItem(this.storageKey);
  }
}
