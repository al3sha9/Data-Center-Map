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
