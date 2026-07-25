import { HttpClient, HttpParams } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

import {
  Category,
  KnowledgeSourceDetail,
  Project,
  SearchRequest,
  SearchResponse,
  Tag,
} from "../shared/models/knowledge.models";

const apiRoot = "/api/v1/knowledge";

@Injectable({ providedIn: "root" })
export class KnowledgeApiService {
  private readonly http = inject(HttpClient);

  categories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${apiRoot}/categories`);
  }

  tags(): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${apiRoot}/tags`);
  }

  autocompleteTags(query: string, limit = 10): Observable<Tag[]> {
    const params = new HttpParams().set("q", query).set("limit", limit);
    return this.http.get<Tag[]>(`${apiRoot}/tags/autocomplete`, { params });
  }

  projects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${apiRoot}/projects`);
  }

  search(request: SearchRequest): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${apiRoot}/search`, request);
  }

  source(sourceId: string): Observable<KnowledgeSourceDetail> {
    return this.http.get<KnowledgeSourceDetail>(`${apiRoot}/sources/${encodeURIComponent(sourceId)}`);
  }
}
