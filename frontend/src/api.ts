export type GeoJSONPolygon = {
  type: 'Polygon'
  coordinates: number[][][]
}

export type Parcel = {
  id: number
  code_insee: string
  prefixe: string
  section: string
  numero: string
  surface_m2: string | number
  geometry: GeoJSONPolygon
  bbox: GeoJSONPolygon
  created_at: string
  updated_at: string
}

export type ParcelCreatePayload = {
  code_insee: string
  prefixe: string
  section: string
  numero: string
  geometry: GeoJSONPolygon
}

export type ParcelUpdatePayload = {
  code_insee?: string
  prefixe?: string
  section?: string
  numero?: string
  geometry?: GeoJSONPolygon
}

export type ParcelSearchPayload = {
  geometry: GeoJSONPolygon
  limit: number
  offset: number
}

type ApiErrorPayload = {
  detail?: {
    code?: string
    message?: string
  }
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://localhost:8000'

const jsonHeaders = {
  'Content-Type': 'application/json',
}

async function parseError(response: Response): Promise<Error> {
  let payload: ApiErrorPayload | null
  try {
    payload = (await response.json()) as ApiErrorPayload
  } catch {
    payload = null
  }

  const detailCode = payload?.detail?.code || 'API_ERROR'
  const detailMessage =
    payload?.detail?.message ||
    `Erreur API (${response.status}) sur ${response.url}`
  return new Error(`[${detailCode}] ${detailMessage}`)
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw await parseError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function checkApiHealth(): Promise<string> {
  const response = await request<{ message: string }>('/health')
  return response.message
}

export async function checkDbHealth(): Promise<string> {
  const response = await request<{ message: string }>('/health/db')
  return response.message
}

export function createParcel(payload: ParcelCreatePayload): Promise<Parcel> {
  return request<Parcel>('/api/parcels', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

export function getParcel(parcelId: number): Promise<Parcel> {
  return request<Parcel>(`/api/parcels/${parcelId}`)
}

export function updateParcel(
  parcelId: number,
  payload: ParcelUpdatePayload,
): Promise<Parcel> {
  return request<Parcel>(`/api/parcels/${parcelId}`, {
    method: 'PATCH',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

export function deleteParcel(parcelId: number): Promise<void> {
  return request<void>(`/api/parcels/${parcelId}`, {
    method: 'DELETE',
  })
}

export function searchParcels(
  payload: ParcelSearchPayload,
): Promise<Parcel[]> {
  return request<Parcel[]>('/api/parcels/search', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  })
}

export function getParcelNeighbors(
  parcelId: number,
  limit: number,
  offset: number,
): Promise<Parcel[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  return request<Parcel[]>(`/api/parcels/${parcelId}/neighbors?${query}`)
}

export { API_BASE_URL }
