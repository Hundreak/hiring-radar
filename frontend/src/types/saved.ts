export type SavedJobStatus = 'reviewing' | 'applied' | 'interview' | 'offer' | 'rejected' | 'archived';

export interface SavedJobNote {
  id: number;
  saved_job_id: number;
  content: string;
  created_at: string | null;
}

export interface SavedJob {
  id: number;
  job_id: number;
  job_kind: 'legacy' | 'canonical';
  status: SavedJobStatus;
  match_score: number | null;
  deadline_at: string | null;
  interview_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  title: string;
  company_name: string;
  location: string | null;
  canonical_url: string;
  source_name: string;
  matched_keywords: string[];
  notes: SavedJobNote[];
}

export interface SavedJobListResponse {
  items: SavedJob[];
  page?: number;
  page_size?: number;
  total_items?: number;
  total_pages?: number;
  status?: SavedJobStatus | null;
}
