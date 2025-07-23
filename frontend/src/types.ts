// API Response Types
export interface Hospital {
  provider_id: string;
  provider_name: string;
  provider_city: string;
  provider_state: string;
  provider_zip_code: string;
  ms_drg_code: string;
  ms_drg_definition: string;
  total_discharges: number;
  average_covered_charges: number;
  average_total_payments: number;
  average_medicare_payments: number;
  average_rating?: number;
  rating?: number;
}

export interface AIResponse {
  answer: string;
  results: Hospital[];
  out_of_scope: boolean;
  sql_query: string | null;
  error: string | null;
}

export interface HealthStatus {
  status: string;
  service: string;
}

// Pagination Types
export interface PaginationInfo {
  page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

// Form State Types
export interface ProviderSearchForm {
  drg: string;
  zip_code: string;
  radius_km: string;
  sort_by: 'cost' | 'rating';
  page: number;
  page_size: number;
}

export interface TextSearchForm {
  q: string;
  zip_code: string;
  radius_km: string;
  page: number;
  page_size: number;
}

// Tab Types
export type TabType = 'providers' | 'text' | 'ai' | 'health';

// Search Result Types
export interface SearchResult {
  hospitals: Hospital[];
  total_count: number;
  search_time_ms?: number;
  query_info?: string;
} 
