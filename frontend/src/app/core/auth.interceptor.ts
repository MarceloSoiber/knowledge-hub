import { HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";

import { AuthService } from "./auth.service";

const protectedApiPrefix = "/api/v1/knowledge/";

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(AuthService).token;

  if (!token || !request.url.startsWith(protectedApiPrefix)) {
    return next(request);
  }

  return next(request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
