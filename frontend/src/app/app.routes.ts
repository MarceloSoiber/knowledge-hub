import { Routes } from "@angular/router";

import { authGuard } from "./core/auth.guard";
import { LoginComponent } from "./features/login/login.component";
import { SearchPageComponent } from "./features/search/search-page.component";
import { SourceDetailComponent } from "./features/source-detail/source-detail.component";
import { AppShellComponent } from "./layout/app-shell.component";

export const routes: Routes = [
  { path: "login", component: LoginComponent },
  {
    path: "",
    component: AppShellComponent,
    canActivate: [authGuard],
    children: [
      { path: "search", component: SearchPageComponent },
      { path: "sources/:sourceId", component: SourceDetailComponent },
      { path: "", pathMatch: "full", redirectTo: "search" },
    ],
  },
  { path: "**", redirectTo: "search" },
];
