export type Currency = "EUR";

export type GigStatus =
  | "open"
  | "claimed"
  | "awaiting_after_photo"
  | "verifying"
  | "approved"
  | "paid"
  | "rejected"
  | "payment_failed";

export type CompletionMode =
  | "fake_local"
  | "real"
  | "ai_fallback"
  | "bunq_fallback";

export type BalanceSource = "bunq" | "fake";

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
};

export type Gig = {
  id: string;
  title: string;
  description: string;
  reward_amount: string;
  currency: Currency;
  status: GigStatus;
  verification_checklist: string[];
  claimed_by_user_id?: string;
  before_photo_id?: string;
};

export type CreateGigRequest = {
  title: string;
  description: string;
  reward_amount: string;
  currency: Currency;
  verification_checklist: string[];
};

export type CreateGigResponse = {
  gig: Pick<Gig, "id" | "status">;
};

export type ListGigsResponse = {
  gigs: Gig[];
};

export type ClaimGigResponse = {
  gig: Pick<Gig, "id" | "status"> & {
    claimed_by_user_id: string;
  };
};

export type BeforePhotoRequest = {
  image_base64: string;
};

export type BeforePhotoResponse = {
  gig: Pick<Gig, "id" | "status"> & {
    before_photo_id: string;
  };
};

export type CompleteGigRequest = {
  after_image_base64: string;
  idempotency_key: string;
};

export type VerificationResult = {
  approved: boolean;
  confidence: number;
  tags: string[];
  message_for_kid: string;
};

export type PaymentResult = {
  status: "succeeded" | "failed";
  amount: string;
  currency: Currency;
  bunq_payment_id?: string;
  retryable?: boolean;
};

export type KidBalance = {
  amount: string;
  currency: Currency;
  source: BalanceSource;
};

export type CompleteGigResponse = {
  gig: Pick<Gig, "id" | "status">;
  verification: VerificationResult;
  payment: PaymentResult | null;
  kid_balance: KidBalance | null;
  mode: CompletionMode;
  fallback_mode: boolean;
};

export type BalanceResponse = {
  balance: KidBalance;
  fallback_mode: boolean;
};

export type IntegrationStatus = {
  mode: string;
  status: "configured" | "not_configured";
  missing_config: string[];
};

export type PathStatus = {
  status: "ok" | "not_ready";
  missing_config: string[];
};

export type HealthResponse = {
  status: "ok" | string;
  readiness_status: "ready" | "not_ready";
  integrations: {
    ai: IntegrationStatus;
    bunq: IntegrationStatus;
    state: PathStatus;
    uploads: PathStatus;
  };
};
