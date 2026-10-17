import { HealthResponse, IncidentSummary, IncidentInvestigationResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function fetchHealth(): Promise<HealthResponse> {
  const url = `${API_BASE}/api/health`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Backend responded with HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchIncidents(): Promise<IncidentSummary[]> {
  const url = `${API_BASE}/api/incidents`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch incidents (HTTP ${response.status})`);
  }

  return response.json();
}

export async function fetchInvestigation(incidentId: string): Promise<IncidentInvestigationResponse> {
  const url = `${API_BASE}/api/incidents/${encodeURIComponent(incidentId)}/investigation`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to investigate incident ${incidentId} (HTTP ${response.status})`);
  }

  return response.json();
}

export async function seedIncidentGraph(): Promise<{ message: string }> {
  const url = `${API_BASE}/api/incidents/seed`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to seed incident graph (HTTP ${response.status})`);
  }

  return response.json();
}
