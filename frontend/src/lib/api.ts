import type { ClaimSummary, ClaimsListResponse, ClaimDetail } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail || `Request failed with status ${res.status}`,
      res.status,
      body
    );
  }

  return res.json();
}

/**
 * Submit a claim with structured JSON data.
 * The backend expects ClaimInputData as a JSON body.
 */
export async function submitClaim(data: Record<string, unknown>): Promise<{ claim_id: string; status: string }> {
  return request("/claims", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

/**
 * Submit a claim with uploaded document files (images/PDFs).
 * Uses multipart/form-data for file upload.
 */
export async function submitClaimWithFiles(
  formData: FormData
): Promise<{ claim_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/claims/upload`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type header — browser sets it with boundary
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail || `Upload failed with status ${res.status}`,
      res.status,
      body
    );
  }

  return res.json();
}

export async function getClaim(claimId: string): Promise<ClaimDetail> {
  return request(`/claims/${claimId}`);
}

export async function getClaims(memberId: string): Promise<ClaimsListResponse> {
  return request(`/claims?member_id=${encodeURIComponent(memberId)}`);
}

export async function appealClaim(claimId: string, reason: string): Promise<{ appeal_id: string; status: string }> {
  return request(`/claims/${claimId}/appeal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export async function getMember(memberId: string): Promise<{
  member_code: string;
  name: string;
  ytd_claimed: number;
  remaining_annual: number;
  remaining_family_floater: number;
  is_active: boolean;
}> {
  return request(`/members/${memberId}`);
}

