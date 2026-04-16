export interface JobListItem {
  id: number;
  source_name: string;
  title: string;
  company_name: string;
  location: string | null;
  canonical_url: string;
  is_active: boolean;
  first_seen_at: string | null;
  last_seen_at: string | null;
  matched: boolean;
  match_score: number | null;
  matched_keywords: string[];
}

export interface JobListResponse {
  items: JobListItem[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  query: string | null;
  only_matched: boolean;
  active_only: boolean;
}
