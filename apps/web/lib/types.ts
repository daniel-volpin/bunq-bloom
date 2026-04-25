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

export type ApiMode = CompletionMode;

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
  after_photo_id?: string;
  created_at?: string;
  updated_at?: string;
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

export type RetryPaymentRequest = {
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

export type RetryPaymentResponse = CompleteGigResponse;

export type BalanceResponse = {
  balance: KidBalance;
  mode: ApiMode;
  fallback_mode: boolean;
};

export type MoneyAmount = {
  amount: string;
  currency: Currency;
};

export type SnapAndLearnRequest = {
  image_base64: string;
};

export type SnapAndLearnAnalysis = {
  item_name: string;
  estimated_price: MoneyAmount;
  gigs_needed: number;
  suggested_goal: string;
  confidence: number | null;
};

export type SnapAndLearnResponse = {
  analysis: SnapAndLearnAnalysis;
  kid_balance: KidBalance;
  mode: ApiMode;
  fallback_mode: boolean;
};

export type BloomReportPeriod = {
  start_date: string;
  end_date: string;
};

export type BloomReportHighlight = {
  title: string;
  detail: string;
};

export type BloomReportStats = {
  gigs_completed: number;
  money_earned: MoneyAmount;
  average_reward: MoneyAmount;
  current_balance: KidBalance;
};

export type BloomReportResponse = {
  period: BloomReportPeriod;
  stats: BloomReportStats;
  highlights: BloomReportHighlight[];
  savings_insight: string;
  conversation_starter: string;
  mode: ApiMode;
  fallback_mode: boolean;
};

export type IntegrationStatus = {
  mode: string;
  ready: boolean;
  status: "configured" | "not_configured";
  missing_config: string[];
};

export type PathStatus = {
  ready?: boolean;
  status: "ok" | "not_ready";
  exists?: boolean;
  readable?: boolean;
  writable?: boolean;
  creatable?: boolean;
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
