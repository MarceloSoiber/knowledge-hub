import { HttpClient, HttpParams } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

import {
  Category,
  CategoryWrite,
  KnowledgeAnswerRequest,
  KnowledgeAnswerResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeSource,
  KnowledgeSourceDetail,
  KnowledgeSourcePatchRequest,
  KnowledgeTextIngestRequest,
  KnowledgeUploadResponse,
  Project,
  ProjectPatch,
  ProjectWrite,
  Tag,
  TagWrite,
} from "./knowledge.types";

@Injectable({ providedIn: "root" })
export class KnowledgeApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = "/api/v1/knowledge";

  categories(): Observable<Category[]> { return this.http.get<Category[]>(`${this.baseUrl}/categories`); }
  createCategory(payload: CategoryWrite): Observable<Category> { return this.http.post<Category>(`${this.baseUrl}/categories`, payload); }
  updateCategory(id: number, payload: CategoryWrite): Observable<Category> { return this.http.patch<Category>(`${this.baseUrl}/categories/${id}`, payload); }
  deleteCategory(id: number): Observable<void> { return this.http.delete<void>(`${this.baseUrl}/categories/${id}`); }
  tags(): Observable<Tag[]> { return this.http.get<Tag[]>(`${this.baseUrl}/tags`); }
  createTag(payload: TagWrite): Observable<Tag> { return this.http.post<Tag>(`${this.baseUrl}/tags`, payload); }
  updateTag(id: number, payload: TagWrite): Observable<Tag> { return this.http.patch<Tag>(`${this.baseUrl}/tags/${id}`, payload); }
  deleteTag(id: number): Observable<void> { return this.http.delete<void>(`${this.baseUrl}/tags/${id}`); }
  tagAutocomplete(query: string, limit = 10): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${this.baseUrl}/tags/autocomplete`, { params: new HttpParams().set("q", query).set("limit", limit) });
  }
  projects(status?: "active" | "archived"): Observable<Project[]> {
    const params = status ? new HttpParams().set("status", status) : undefined;
    return this.http.get<Project[]>(`${this.baseUrl}/projects`, { params });
  }
  createProject(payload: ProjectWrite): Observable<Project> { return this.http.post<Project>(`${this.baseUrl}/projects`, payload); }
  updateProject(id: number, payload: ProjectPatch): Observable<Project> { return this.http.patch<Project>(`${this.baseUrl}/projects/${id}`, payload); }
  archiveProject(id: number): Observable<Project> { return this.http.post<Project>(`${this.baseUrl}/projects/${id}/archive`, {}); }
  reactivateProject(id: number): Observable<Project> { return this.http.post<Project>(`${this.baseUrl}/projects/${id}/reactivate`, {}); }
  projectSources(id: number): Observable<KnowledgeSource[]> { return this.http.get<KnowledgeSource[]>(`${this.baseUrl}/projects/${id}/sources`); }
  sources(): Observable<KnowledgeSource[]> { return this.http.get<KnowledgeSource[]>(`${this.baseUrl}/sources`); }
  source(sourceId: string): Observable<KnowledgeSourceDetail> { return this.http.get<KnowledgeSourceDetail>(`${this.baseUrl}/sources/${encodeURIComponent(sourceId)}`); }
  updateSource(sourceId: string, payload: KnowledgeSourcePatchRequest): Observable<KnowledgeSourceDetail> {
    return this.http.patch<KnowledgeSourceDetail>(`${this.baseUrl}/sources/${encodeURIComponent(sourceId)}`, payload);
  }
  deleteSource(sourceId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/sources/${encodeURIComponent(sourceId)}`, { params: new HttpParams().set("confirm", "true") });
  }
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
  backup(): Observable<Blob> { return this.http.get(`${this.baseUrl.replace("/knowledge", "/operations")}/backup`, { responseType: "blob" }); }
  restoreBackup(file: File, confirmation: string): Observable<{ message: string; safety_backup: string }> {
    const data = new FormData(); data.append("file", file); data.append("confirmation", confirmation);
    return this.http.post<{ message: string; safety_backup: string }>(`${this.baseUrl.replace("/knowledge", "/operations")}/restore`, data);
  }
}
