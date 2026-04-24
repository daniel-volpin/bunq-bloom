import type {
  ApiErrorBody,
  BalanceResponse,
  BeforePhotoRequest,
  BeforePhotoResponse,
  ClaimGigResponse,
  CompleteGigRequest,
  CompleteGigResponse,
  CreateGigRequest,
  CreateGigResponse,
  Gig,
  HealthResponse,
  ListGigsResponse
} from "@/lib/types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiClientError extends Error {
  code: string;
  retryable: boolean;
  status: number;

  constructor(message: string, code: string, retryable: boolean, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.retryable = retryable;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    }
  });

  const body = (await response.json().catch(() => null)) as T | ApiErrorBody | null;

  if (!response.ok) {
    const errorBody = body as ApiErrorBody | null;
    throw new ApiClientError(
      errorBody?.error.message ?? "Something went wrong. Try again.",
      errorBody?.error.code ?? "unknown_error",
      errorBody?.error.retryable ?? true,
      response.status
    );
  }

  return body as T;
}

export const apiClient = {
  getHealth: () => request<HealthResponse>("/api/health"),

  listGigs: () => request<ListGigsResponse>("/api/gigs"),

  async getGig(gigId: string): Promise<Gig | null> {
    const { gigs } = await apiClient.listGigs();
    return gigs.find((gig) => gig.id === gigId) ?? null;
  },

  createGig: (payload: CreateGigRequest) =>
    request<CreateGigResponse>("/api/gigs", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  claimGig: (gigId: string) =>
    request<ClaimGigResponse>(`/api/gigs/${gigId}/claim`, {
      method: "POST"
    }),

  uploadBeforePhoto: (gigId: string, payload: BeforePhotoRequest) =>
    request<BeforePhotoResponse>(`/api/gigs/${gigId}/before-photo`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  completeGig: (gigId: string, payload: CompleteGigRequest) =>
    request<CompleteGigResponse>(`/api/gigs/${gigId}/complete`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  getKidBalance: () => request<BalanceResponse>("/api/balance/kid")
};
