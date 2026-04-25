# API Contracts

The frontend calls the FastAPI backend through a Next.js `/api/*` proxy.

All responses should include JSON. Errors should use a consistent shape:

```json
{
  "error": {
    "code": "payment_failed",
    "message": "Payment could not be completed. Try again.",
    "retryable": true
  }
}
```

Common error codes:

- `invalid_gig_state`
- `missing_before_photo`
- `image_too_large`
- `invalid_image_type`
- `verification_failed`
- `payment_failed`
- `payment_state_unknown`
- `payment_not_retryable`
- `duplicate_completion`

Image upload constraints:

- Accepted content types: `image/jpeg`, `image/png`, `image/webp`
- Max original upload size: 8 MB
- The API can receive base64 for MVP speed, but backend storage should persist files under `data/uploads/` and store references in JSON.

## Gig APIs

### `GET /api/gigs`

Returns gigs for the current MVP family.

Response:

```json
{
  "gigs": [
    {
      "id": "gig_001",
      "title": "Clean your room",
      "description": "Make the bed, clear the floor, and tidy the desk.",
      "reward_amount": "5.00",
      "currency": "EUR",
      "status": "open",
      "verification_checklist": ["bed made", "floor clear", "desk tidy"]
    }
  ]
}
```

### `POST /api/gigs`

Creates a gig. Parent flow only in the product, but auth can be stubbed for MVP.

Request:

```json
{
  "title": "Clean your room",
  "description": "Make the bed, clear the floor, and tidy the desk.",
  "reward_amount": "5.00",
  "currency": "EUR",
  "verification_checklist": ["bed made", "floor clear", "desk tidy"]
}
```

Response:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "open"
  }
}
```

### `POST /api/gigs/{gig_id}/claim`

Claims an open gig for the kid.

Response:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "claimed",
    "claimed_by_user_id": "kid_001"
  }
}
```

### `POST /api/gigs/{gig_id}/before-photo`

Stores the before photo and prepares the gig for completion.

Request:

```json
{
  "image_base64": "data:image/jpeg;base64,..."
}
```

Response:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "awaiting_after_photo",
    "before_photo_id": "photo_before_001"
  }
}
```

### `POST /api/gigs/{gig_id}/complete`

The core endpoint. Submits the after photo, runs AI verification, pays the kid if approved, and returns the updated balance.

Request:

```json
{
  "after_image_base64": "data:image/jpeg;base64,...",
  "idempotency_key": "completion_2026_04_25_001"
}
```

Response on approval and payment success:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "paid"
  },
  "verification": {
    "approved": true,
    "confidence": 0.91,
    "tags": ["bed made", "floor clear", "desk tidy"],
    "message_for_kid": "Nice work. Your room looks much tidier."
  },
  "payment": {
    "status": "succeeded",
    "amount": "5.00",
    "currency": "EUR",
    "bunq_payment_id": "12345"
  },
  "kid_balance": {
    "amount": "27.50",
    "currency": "EUR",
    "source": "bunq"
  },
  "mode": "real",
  "ai_mode": "real",
  "payment_mode": "real",
  "fallback_mode": false
}
```

Response on AI rejection:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "rejected"
  },
  "verification": {
    "approved": false,
    "confidence": 0.74,
    "tags": ["bed made"],
    "message_for_kid": "The bed looks better, but the floor still needs tidying."
  },
  "payment": null,
  "kid_balance": null,
  "mode": "real",
  "ai_mode": "real",
  "payment_mode": "real",
  "fallback_mode": false
}
```

Response on payment failure after approval:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "payment_failed"
  },
  "verification": {
    "approved": true,
    "confidence": 0.91,
    "tags": ["bed made", "floor clear", "desk tidy"],
    "message_for_kid": "Nice work. Your room looks much tidier."
  },
  "payment": {
    "status": "failed",
    "amount": "5.00",
    "currency": "EUR",
    "retryable": true
  },
  "kid_balance": null,
  "mode": "real",
  "ai_mode": "real",
  "payment_mode": "real",
  "fallback_mode": false
}
```

Mode values:

- `fake_local`: local fake payment mode was used, even if AI was real
- `real`: both AI and payment path used real configured providers
- `ai_fallback`: Claude failed and explicit demo fallback was used
- `bunq_fallback`: bunq failed and explicit demo fallback was used

`ai_mode` and `payment_mode` expose the two integration paths separately. Frontend copy should not claim real money moved unless `payment_mode` is `real`.

If the bunq payment succeeds but the follow-up balance refresh fails, the gig still returns `status: paid` with the successful payment and adds `balance_refresh_status: failed`. Retrying must not create a second payment.

### `POST /api/gigs/{gig_id}/retry-payment`

Retries payment for a gig that is already AI-approved but currently in `payment_failed`.

Request:

```json
{
  "idempotency_key": "retry_payment_2026_04_25_001"
}
```

Response on payment retry success:

```json
{
  "gig": {
    "id": "gig_001",
    "status": "paid"
  },
  "verification": {
    "approved": true,
    "confidence": 0.91,
    "tags": ["bed made", "floor clear", "desk tidy"],
    "message_for_kid": "Nice work. Your room looks much tidier."
  },
  "payment": {
    "status": "succeeded",
    "amount": "5.00",
    "currency": "EUR",
    "bunq_payment_id": "12346"
  },
  "kid_balance": {
    "amount": "27.50",
    "currency": "EUR",
    "source": "bunq"
  },
  "mode": "real",
  "ai_mode": "real",
  "payment_mode": "real",
  "fallback_mode": false
}
```

Error cases:

- `invalid_gig_state` when the gig is not currently `payment_failed`
- `payment_failed` when the retry attempt also fails
- `payment_not_retryable` when bunq may have created a payment but returned an unparseable response

## Money APIs

### `GET /api/balance/kid`

Returns the kid account balance.

Response:

```json
{
  "balance": {
    "amount": "22.50",
    "currency": "EUR",
    "source": "bunq"
  },
  "fallback_mode": false
}
```

## Snap & Learn APIs

### `POST /api/snap-and-learn/analyze`

Analyzes a photographed item, estimates its price, compares it with the kid balance, and translates the gap into gigs needed.

Request:

```json
{
  "image_base64": "data:image/jpeg;base64,..."
}
```

Response:

```json
{
  "analysis": {
    "item_name": "Nintendo Switch Game",
    "estimated_price": {
      "amount": "24.99",
      "currency": "EUR"
    },
    "gigs_needed": 1,
    "suggested_goal": "Save for Nintendo Switch Game by completing 1 more gig.",
    "confidence": 0.91
  },
  "kid_balance": {
    "amount": "22.50",
    "currency": "EUR",
    "source": "fake"
  },
  "mode": "fake_local",
  "ai_mode": "real",
  "payment_mode": "fake_local",
  "fallback_mode": false
}
```

## Bloom Report APIs

### `GET /api/bloom-report/weekly`

Returns the current week's family recap with stats, highlights, a savings insight, and a conversation starter.

Response:

```json
{
  "period": {
    "start_date": "2026-04-19",
    "end_date": "2026-04-25"
  },
  "stats": {
    "gigs_completed": 2,
    "money_earned": {
      "amount": "12.50",
      "currency": "EUR"
    },
    "average_reward": {
      "amount": "6.25",
      "currency": "EUR"
    },
    "current_balance": {
      "amount": "35.00",
      "currency": "EUR",
      "source": "fake"
    }
  },
  "highlights": [
    {
      "title": "Family win",
      "detail": "Two gigs turned effort into EUR 12.50 this week."
    }
  ],
  "savings_insight": "EUR 12.50 earned means EUR 6.25 could go straight into savings this week.",
  "conversation_starter": "Which reward felt most worth the effort this week?",
  "mode": "fake_local",
  "fallback_mode": false
}
```

## Health APIs

### `GET /api/health`

Returns app health and integration status.

Response:

```json
{
  "status": "ok",
  "readiness_status": "ready",
  "integrations": {
    "ai": {
      "mode": "real",
      "ready": true,
      "status": "configured",
      "missing_config": []
    },
    "bunq": {
      "mode": "fake",
      "ready": true,
      "status": "configured",
      "missing_config": []
    },
    "state": {
      "ready": true,
      "status": "ok",
      "path_parent": {
        "ready": true,
        "status": "ok",
        "exists": true,
        "readable": true,
        "writable": true,
        "creatable": true,
        "missing_config": []
      },
      "missing_config": []
    },
    "uploads": {
      "ready": true,
      "status": "ok",
      "exists": true,
      "readable": true,
      "writable": true,
      "creatable": true,
      "missing_config": []
    }
  }
}
```
