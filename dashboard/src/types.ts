export interface IncidentSummary {
  id: string;
  timestamp: string;
  top_root_cause: string;
  confidence_pct: number;
}

export interface RootCauseEvidence {
  causal_edges?: number;
  log_errors_before?: number;
  anomaly_at?: number | null;
}

export interface RootCause {
  rank: number;
  service: string;
  metric: string;
  confidence_pct: number;
  evidence: RootCauseEvidence;
}

export interface IncidentDetail {
  id: string;
  created_at: string;
  incident_start: number;
  incident_start_iso: string;
  root_causes: RootCause[];
  llm_explanation?: string | null;
  event_count: number;
  log_files: string[];
  metrics_file?: string | null;
}

export interface GraphNode {
  id: string;
  name: string;
  role: 'root_cause' | 'affected' | 'healthy';
}

export interface GraphLink {
  source: string;
  target: string;
  confidence: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
