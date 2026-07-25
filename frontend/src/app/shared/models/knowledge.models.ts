export interface Category {
  id: number;
  name: string;
}

export interface Tag extends Category {}

export interface Project extends Category {
  description: string | null;
  status: "active" | "archived";
  created_at: string | null;
  updated_at: string | null;
}

export interface KnowledgeLocation {
  chunk_index: number;
  page: number | null;
  section: string | null;
  start_char: number;
  end_char: number;
}

export interface KnowledgeSearchResult {
  id: number;
  source_id: string;
  source_title: string;
  source_type: string;
  uri: string;
  categories: Category[];
  tags: Tag[];
  projects: Project[];
  location: KnowledgeLocation;
  content: string;
  score: number | null;
  metadata: Record<string, unknown>;
  match_reasons?: Array<"vector" | "text">;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  category_ids?: number[];
  tag_ids?: number[];
  project_ids?: number[];
  min_score?: number;
  include_match_reasons?: boolean;
}

export interface SearchResponse {
  query: string;
  limit: number;
  results: KnowledgeSearchResult[];
}

export interface KnowledgeSourceDetail {
  source_id: string;
  title: string;
  categories: Category[];
  tags: Tag[];
  projects: Project[];
  source_type: string;
  uri: string;
  content_hash: string;
  content: string;
}
