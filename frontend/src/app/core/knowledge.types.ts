export interface Category {
  id: number;
  name: string;
}

export interface Tag extends Category {}

export interface CategoryWrite { name: string; }
export interface TagWrite { name: string; }

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: "active" | "archived";
  created_at: string | null;
  updated_at: string | null;
}

export interface ProjectWrite { name: string; description?: string | null; }
export interface ProjectPatch { name?: string; description?: string | null; }

export interface KnowledgeSource {
  source_id: string;
  title: string;
  categories: Category[];
  tags: Tag[];
  projects: Project[];
  source_type: string;
  uri: string;
  content_hash: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface KnowledgeSourceDetail extends KnowledgeSource {
  content: string;
}

export interface KnowledgeSourcePatchRequest {
  title?: string;
  content?: string;
  category_ids?: number[];
  tag_ids?: number[];
  project_ids?: number[];
}

export interface KnowledgeChunkLocation {
  chunk_index: number;
  page: number | null;
  section: string | null;
  start_char: number;
  end_char: number;
}

export interface KnowledgeChunk {
  id: number;
  source_id: string;
  source_title: string;
  source_type: string;
  uri: string;
  categories: Category[];
  tags: Tag[];
  projects: Project[];
  location: KnowledgeChunkLocation;
  content: string;
  score: number | null;
  metadata: Record<string, unknown>;
  match_reasons?: Array<"vector" | "text">;
}

export interface KnowledgeFilters {
  category_ids?: number[];
  tag_ids?: number[];
  project_ids?: number[];
  min_score?: number;
}

export interface KnowledgeSearchRequest extends KnowledgeFilters {
  query: string;
  limit?: number;
  include_match_reasons?: boolean;
}

export interface KnowledgeSearchResponse {
  query: string;
  limit: number;
  results: KnowledgeChunk[];
}

export interface KnowledgeAnswerRequest extends KnowledgeFilters {
  query: string;
  limit?: number;
  include_match_reasons?: boolean;
}

export interface KnowledgeAnswerResponse {
  query: string;
  answer: string;
  sources: KnowledgeChunk[];
}

export interface KnowledgeTextIngestRequest {
  title: string;
  content: string;
  category_ids: number[];
  tag_ids?: number[];
  project_ids?: number[];
}

export interface KnowledgeUploadResponse {
  source_id: string;
  title: string;
  categories: Category[];
  tags: Tag[];
  projects: Project[];
  chunks_created: number;
}

export interface MetadataSelection {
  categoryIds: number[];
  tagIds: number[];
  projectIds: number[];
}
