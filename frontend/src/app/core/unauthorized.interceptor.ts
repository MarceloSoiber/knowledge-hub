import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { Router } from "@angular/router";
import { catchError, throwError } from "rxjs";

import { AuthService } from "./auth.service";

export const unauthorizedInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(request).pipe(catchError((error: unknown) => {
    if (error instanceof HttpErrorResponse && error.status === 401 && request.url.startsWith("/api/v1/knowledge/")) {
      auth.logout();
      if (!router.url.startsWith("/login")) {
        void router.navigate(["/login"]);
      }
    }
    return throwError(() => error);
  }));
};
