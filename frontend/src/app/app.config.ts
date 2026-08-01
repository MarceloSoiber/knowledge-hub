import { ApplicationConfig, inject, provideAppInitializer } from "@angular/core";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import { provideRouter } from "@angular/router";

import { authInterceptor } from "./core/auth.interceptor";
import { AuthService } from "./core/auth.service";
import { routes } from "./app.routes";

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor])),
    provideRouter(routes),
    provideAppInitializer(() => inject(AuthService).initialize()),
  ],
};
