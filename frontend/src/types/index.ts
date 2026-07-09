export interface Filters {
  province?: string;
  district?: string;
  start_date?: string;
  end_date?: string;
}

export interface AggregatedData {
  total_facilities: number;
  avg_hts_mohcc_pct: number | null;
  avg_vl_mohcc_pct: number | null;
  categorical: Record<string, Record<string, number>>;
}

export interface Insight {
  summary: string;
  categories: string[];
  challenges: string[];
  mitigations: string[];
}