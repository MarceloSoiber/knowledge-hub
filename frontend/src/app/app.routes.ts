import { Routes } from "@angular/router";

import { authGuard } from "./core/auth.guard";
import { HomeComponent } from "./features/home/home.component";
import { LoginComponent } from "./features/login/login.component";
import { SearchPageComponent } from "./features/search/search-page.component";
import { AskPageComponent } from "./features/ask/ask-page.component";
import { IngestionPageComponent } from "./features/ingestion/ingestion-page.component";
import { SourceDetailComponent } from "./features/source-detail/source-detail.component";
import { LibraryPageComponent } from "./features/library/library-page.component";
import { OrganizationPageComponent } from "./features/organization/organization-page.component";
import { ProjectSourcesComponent } from "./features/organization/project-sources.component";
import { OperationsPageComponent } from "./features/operations/operations-page.component";
import { AuthenticatedLayoutComponent } from "./layout/authenticated-layout.component";

export const routes: Routes = [
  { path: "login", component: LoginComponent, title: "Acessar | Knowledge Hub" },
  {
    path: "",
    component: AuthenticatedLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: "inicio", component: HomeComponent, title: "Início | Knowledge Hub" },
      { path: "busca", component: SearchPageComponent, title: "Busca inteligente | Knowledge Hub" },
      { path: "perguntar", component: AskPageComponent, title: "Pergunte à base | Knowledge Hub" },
      { path: "ingestao", component: IngestionPageComponent, title: "Ingestão | Knowledge Hub" },
      { path: "biblioteca", component: LibraryPageComponent, title: "Biblioteca | Knowledge Hub" },
      { path: "organizacao", component: OrganizationPageComponent, title: "Organização | Knowledge Hub" },
      { path: "operacoes", component: OperationsPageComponent, title: "Backup e restauração | Knowledge Hub" },
      { path: "organizacao/projetos/:projectId/fontes", component: ProjectSourcesComponent, title: "Fontes do projeto | Knowledge Hub" },
      { path: "sources/:sourceId", component: SourceDetailComponent, title: "Fonte | Knowledge Hub" },
      { path: "", pathMatch: "full", redirectTo: "inicio" },
    ],
  },
  { path: "**", redirectTo: "" },
];
