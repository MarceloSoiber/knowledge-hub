import { CanActivateFn, Router } from "@angular/router";
import { inject } from "@angular/core";

import { AuthService } from "./auth.service";

export const authGuard: CanActivateFn = async (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  await auth.initialize();
  return auth.isAuthenticated
    ? true
    : router.createUrlTree(["/login"], { queryParams: { returnUrl: state.url } });
};
