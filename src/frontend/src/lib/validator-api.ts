/**
 * validator-api.ts
 *
 * Typed wrappers for the two new validator endpoints.
 * Drop this file alongside your existing src/lib/api.ts — it re-uses
 * the same `apiFetch` helper so cookie/auth handling is unchanged.
 *
 * Existing callers of apiFetch are unaffected.
 */

import { apiFetch } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ValidatorIncident {
  incident_id: number;
  verification_status: "DRAFT" | "PENDING" | "PENDING_VALIDATION" | "VERIFIED" | "REJECTED";
  encoder_id: string | null;
  region_id: number;
  created_at: string | null;
  notification_dt: string | null;
  general_category: string | null;
  alarm_level: string | null;
  fire_station_name: string | null;
  structures_affected: number | null;
  households_affected: number | null;
  responder_type: string | null;
  fire_origin: string | null;
  extent_of_damage: string | null;
}

export interface ValidatorQueueResponse {
  items: ValidatorIncident[];
  total: number;
  limit: number;
  offset: number;
}

export interface ValidatorQueueParams {
  /** Filter by a single verification_status.
   *  Omit to get the default queue (PENDING + PENDING_VALIDATION). */
  status?: string;
  /** Filter by encoder UUID (full UUID string). */
  encoder_id?: string;
  limit?: number;
  offset?: number;
}

export type ValidatorAction = "accept" | "pending" | "reject";

export interface VerificationActionRequest {
  /** "accept" → VERIFIED, "pending" → PENDING, "reject" → REJECTED */
  action: ValidatorAction;
  /** Optional free-text notes stored in incident_verification_history. */
  notes?: string | null;
}

export interface VerificationActionResponse {
  incident_id: number;
  previous_status: string;
  new_status: string;
  action: ValidatorAction;
  encoder_id: string;
  region_id: number;
}

// ---------------------------------------------------------------------------
// GET /api/regional/validator/incidents
// ---------------------------------------------------------------------------

/**
 * Fetch the validator's region-scoped incident queue.
 *
 * Only returns incidents where encoder_id IS NOT NULL (encoder-submitted).
 * Region filtering is enforced server-side via the validator's assigned_region_id.
 *
 * @throws on 4xx/5xx — pass the error message to your UI error state.
 */
export async function fetchValidatorQueue(
  params: ValidatorQueueParams = {}
): Promise<ValidatorQueueResponse> {
  const qs = new URLSearchParams();
  if (params.status)     qs.set("status",     params.status);
  if (params.encoder_id) qs.set("encoder_id", params.encoder_id);
  if (params.limit  != null) qs.set("limit",  String(params.limit));
  if (params.offset != null) qs.set("offset", String(params.offset));

  const query = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<ValidatorQueueResponse>(
    `/api/regional/validator/incidents${query}`
  );
}

// ---------------------------------------------------------------------------
// PATCH /api/regional/incidents/:id/verification
// ---------------------------------------------------------------------------

/**
 * Apply a validator decision to one incident.
 *
 * Preconditions (enforced server-side — these raise 4xx if violated):
 *  - Caller must be NATIONAL_VALIDATOR with assigned_region_id.
 *  - Incident must belong to validator's region.
 *  - Incident must have encoder_id IS NOT NULL.
 *  - Incident must not already be in the target status (409 guard).
 *
 * @param incidentId  fire_incidents.incident_id
 * @param body        { action: "accept"|"pending"|"reject", notes?: string }
 * @returns           Updated status payload from the server.
 */
export async function submitVerificationAction(
  incidentId: number,
  body: VerificationActionRequest
): Promise<VerificationActionResponse> {
  return apiFetch<VerificationActionResponse>(
    `/api/regional/incidents/${incidentId}/verification`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    }
  );
}
