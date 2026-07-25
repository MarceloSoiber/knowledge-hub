import { HttpClient, HttpParams } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

import {
  Category,
  KnowledgeAnswerRequest,
  KnowledgeAnswerResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeSource,
  KnowledgeSourceDetail,
  KnowledgeTextIngestRequest,
  KnowledgeUploadResponse,
  Project,
  Tag,
} from "./knowledge.types";

@Injectable({ providedIn: "root" })
export class KnowledgeApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = "/api/v1/knowledge";

  categories(): Observable<Category[]> { return this.http.get<Category[]>(`${this.baseUrl}/categories`); }
  tags(): Observable<Tag[]> { return this.http.get<Tag[]>(`${this.baseUrl}/tags`); }
  tagAutocomplete(query: string, limit = 10): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${this.baseUrl}/tags/autocomplete`, { params: new HttpParams().set("q", query).set("limit", limit) });
  }
  projects(status?: "active" | "archived"): Observable<Project[]> {
    const params = status ? new HttpParams().set("status", status) : undefined;
    return this.http.get<Project[]>(`${this.baseUrl}/projects`, { params });
  }
  sources(): Observable<KnowledgeSource[]> { return this.http.get<KnowledgeSource[]>(`${this.baseUrl}/sources`); }
  source(sourceId: string): Observable<KnowledgeSourceDetail> { return this.http.get<KnowledgeSourceDetail>(`${this.baseUrl}/sources/${encodeURIComponent(sourceId)}`); }
  search(payload: KnowledgeSearchRequest): Observable<KnowledgeSearchResponse> { return this.http.post<KnowledgeSearchResponse>(`${this.baseUrl}/search`, payload); }
  answer(payload: KnowledgeAnswerRequest): Observable<KnowledgeAnswerResponse> { return this.http.post<KnowledgeAnswerResponse>(`${this.baseUrl}/answer`, payload); }
  ingestText(payload: KnowledgeTextIngestRequest): Observable<KnowledgeUploadResponse> { return this.http.post<KnowledgeUploadResponse>(`${this.baseUrl}/texts`, payload); }
  upload(file: File, categoryIds: number[], tagIds: number[] = [], projectIds: number[] = []): Observable<KnowledgeUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    categoryIds.forEach((id) => formData.append("category_ids", String(id)));
    tagIds.forEach((id) => formData.append("tag_ids", String(id)));
    projectIds.forEach((id) => formData.append("project_ids", String(id)));
    return this.http.post<KnowledgeUploadResponse>(`${this.baseUrl}/uploads`, formData);
  }
}
