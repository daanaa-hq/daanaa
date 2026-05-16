const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface Organization {
  EIN: string;
  organization_name: string;
  NTEE1: string;
  CITY: string;
  STATE: string;
  total_revenue: number;
  total_revenue_formatted: string;
  ntee1_percentile: number;
  source: string;
}

export interface OrgDetail extends Organization {
  similar_organizations: Organization[];
  category_rank?: number;
  category_total?: number;
}

export interface PaginatedOrgs {
  organizations: Organization[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export async function fetchOrgs(params: Record<string, string> = {}): Promise<PaginatedOrgs> {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/organizations?${qs}`);
  if (!res.ok) throw new Error('Failed to fetch organizations');
  return res.json();
}

export async function fetchOrg(ein: string): Promise<OrgDetail> {
  const res = await fetch(`${API_BASE}/api/organizations/${ein}`);
  if (!res.ok) throw new Error('Not found');
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch(`${API_BASE}/api/ntee-categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}
