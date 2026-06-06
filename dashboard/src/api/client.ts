import type { GraphData, IncidentDetail, IncidentSummary } from '../types';

const API_BASE = process.env.REACT_APP_API_URL ?? '';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function fetchIncidents(): Promise<IncidentSummary[]> {
  const response = await fetch(`${API_BASE}/api/incidents`);
  return handleResponse<IncidentSummary[]>(response);
}

export async function fetchIncident(id: string): Promise<IncidentDetail> {
  const response = await fetch(`${API_BASE}/api/incidents/${id}`);
  return handleResponse<IncidentDetail>(response);
}

export async function fetchIncidentGraph(id: string): Promise<GraphData> {
  const response = await fetch(`${API_BASE}/api/incidents/${id}/graph`);
  return handleResponse<GraphData>(response);
}

export interface RunAnalysisRequest {
  log_paths: string[];
  metrics_path?: string;
  since?: string;
  explain?: boolean;
}

export async function runAnalysis(request: RunAnalysisRequest): Promise<{ id: string }> {
  const response = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const report = await handleResponse<{ id: string }>(response);
  return { id: report.id };
}
