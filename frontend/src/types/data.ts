export interface EnergyRecord {
  id: string;
  year: number;
  region: string;
  country: string | null;
  metric: string;
  value: number;
  unit: string;
  scenario: string;
  source_id: string;
  source_label: string;
  source_page: number;
  confidence: "high" | "medium" | "low";
  note: string;
}

export interface Source {
  id: string;
  name: string;
  publisher: string | null;
  type: string;
  year: number | null;
  url: string | null;
  filename: string;
  credibility: string;
  notes: string;
}

export interface Meta {
  version: string;
  last_updated: string;
  total_records: number;
  source_count: number;
  metrics: string[];
  coverage: {
    years: number[];
    regions: string[];
    countries: string[];
  };
  disclaimer: string;
}

export interface ModelComparisonRecord {
  id: string;
  scope: string;
  institution: string;
  publication: string;
  year: number;
  value_twh: number | null;
  value_min_twh: number | null;
  value_max_twh: number | null;
  projection_year: number | null;
  includes_crypto: boolean | null;
  includes_ai: boolean | null;
  method_summary: string;
  quality_assessment: string;
  note: string;
  source: string;
}

export interface UsModelComparisonRecord {
  id: string;
  scope: string;
  institution: string;
  publication: string;
  year: number | null;
  value_twh: number | null;
  value_min_twh: number | null;
  value_max_twh: number | null;
  projection_year: number | null;
  ai_value_twh: number | null;
  ai_value_min_twh: number | null;
  ai_value_max_twh: number | null;
  share_percent: number | null;
  method_summary: string;
  quality_assessment: string;
  note: string;
  source: string;
}

export interface RegionalDemandRecord {
  id: string;
  region: string;
  country: string | null;
  year: number;
  value_twh: number | null;
  value_min_twh: number | null;
  value_max_twh: number | null;
  projection_year: number | null;
  share_percent: number | null;
  metric: string;
  scenario: string;
  quality_assessment: string;
  note: string;
  source: string;
}
