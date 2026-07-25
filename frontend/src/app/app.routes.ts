import { Routes } from "@angular/router";

import { authGuard } from "./core/auth.guard";
import { HomeComponent } from "./features/home/home.component";
import { LoginComponent } from "./features/login/login.component";
import { AuthenticatedLayoutComponent } from "./layout/authenticated-layout.component";

export const routes: Routes = [
  { path: "login", component: LoginComponent, title: "Acessar | Knowledge Hub" },
  {
    path: "",
    component: AuthenticatedLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: "inicio", component: HomeComponent, title: "Início | Knowledge Hub" },
      { path: "", pathMatch: "full", redirectTo: "inicio" },
    ],
  },
  { path: "**", redirectTo: "" },
];
