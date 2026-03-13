/**
 * Fetch-based API client for FastAPI backend.
 * Uses credentials: 'include' for cookie-based auth.
 */
const API_BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || '/api')
  : process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((json as { message?: string; detail?: string }).message ?? (json as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return json as T;
}

/** Fetch incidents list - returns [] on error or 404 */
export async function fetchIncidents(params?: { region_id?: number; category?: string; from?: string; to?: string; type?: string }): Promise<any[]> {
  try {
    const search = new URLSearchParams();
    if (params?.region_id) search.set('region_id', String(params.region_id));
    if (params?.category) search.set('category', params.category);
    if (params?.from) search.set('from', params.from);
    if (params?.to) search.set('to', params.to);
    if (params?.type) search.set('type', params.type);
    const qs = search.toString();
    const data = await apiFetch<{ data?: any[]; items?: any[] } | any[]>(`/incidents${qs ? `?${qs}` : ''}`);
    return Array.isArray(data) ? data : (data?.data ?? data?.items ?? []);
  } catch {
    return [];
  }
}

/** Fetch single incident - returns null on error */
export async function fetchIncident(id: number): Promise<any | null> {
  try {
    return await apiFetch<any>(`/incidents/${id}`);
  } catch {
    return null;
  }
}

/** Fetch reference regions - returns [] on error */
export async function fetchRegions(): Promise<any[]> {
  try {
    const data = await apiFetch<any[] | { data?: any[] }>('/ref/regions');
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch provinces by region - returns [] on error */
export async function fetchProvinces(regionId: string | number): Promise<any[]> {
  try {
    const data = await apiFetch<any[] | { data?: any[] }>(`/ref/provinces?region_id=${regionId}`);
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch cities by province - returns [] on error */
export async function fetchCities(provinceId: string | number): Promise<any[]> {
  try {
    const data = await apiFetch<any[] | { data?: any[] }>(`/ref/cities?province_id=${provinceId}`);
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch cities by multiple province IDs - returns [] on error */
export async function fetchCitiesByProvinces(provinceIds: number[]): Promise<any[]> {
  if (provinceIds.length === 0) return [];
  try {
    const data = await apiFetch<any[] | { data?: any[] }>(`/ref/cities?province_ids=${provinceIds.join(',')}`);
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch barangays by city IDs - returns [] on error */
export async function fetchBarangays(cityIds: number[]): Promise<any[]> {
  if (cityIds.length === 0) return [];
  try {
    const data = await apiFetch<any[] | { data?: any[] }>(`/ref/barangays?city_ids=${cityIds.join(',')}`);
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch regions filtered by region_id - returns [] on error */
export async function fetchRegionsByRegionId(regionId: number): Promise<any[]> {
  try {
    const data = await apiFetch<any[] | { data?: any[] }>(`/ref/regions?region_id=${regionId}`);
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}

/** Fetch security threat logs - returns [] on error */
export async function fetchSecurityLogs(): Promise<any[]> {
  try {
    const data = await apiFetch<any[] | { data?: any[] }>('/security-threat-logs');
    return Array.isArray(data) ? data : (data?.data ?? []);
  } catch {
    return [];
  }
}
