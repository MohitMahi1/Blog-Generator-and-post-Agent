export interface Task {
  id: number;
  title: string;
  goal: string;
  bullets: string[];
  target_words: number;
  tags: string[];
  requires_research: boolean;
  requires_citations: boolean;
  requires_code: boolean;
}

export interface Plan {
  blog_title: string;
  audience: string;
  tone: string;
  blog_kind: string;
  constraints: string[];
  tasks: Task[];
}

export interface EvidenceItem {
  title: string;
  url: string;
  published_at?: string | null;
  snippet?: string | null;
  source?: string | null;
}

export interface ImageSpec {
  placeholder: string;
  filename: string;
  alt: string;
  caption: string;
  prompt: string;
  size: string;
  quality: string;
}

export interface GenerateResponse {
  blog_id?: string | null;
  session_id?: string | null;
  blog_title: string;
  final_markdown: string;
  mode: string;
  needs_research: boolean;
  sections_count: number;
  plan?: Plan | null;
  queries?: string[];
  evidence?: EvidenceItem[];
  image_specs?: ImageSpec[];
  logs?: string[];
}

export interface BlogListItem {
  blog_id: string;
  blog_title: string;
  created_at: string;
  session_id: string;
}

export interface BlogListResponse {
  blogs: BlogListItem[];
}