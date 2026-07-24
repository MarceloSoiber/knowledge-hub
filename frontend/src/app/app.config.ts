import { ApplicationConfig } from "@angular/core";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import { provideRouter, withInMemoryScrolling } from "@angular/router";

import { authInterceptor } from "./core/auth.interceptor";
import { unauthorizedInterceptor } from "./core/unauthorized.interceptor";
import { routes } from "./app.routes";

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor, unauthorizedInterceptor])),
    provideRouter(routes, withInMemoryScrolling({ scrollPositionRestoration: "top" })),
  ],
};
