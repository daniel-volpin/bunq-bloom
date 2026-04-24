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
  "fallback_mode": false
}
```

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

## Health APIs

### `GET /api/health`

Returns app health and integration status.

Response:

```json
{
  "status": "ok",
  "integrations": {
    "claude": "configured",
    "bunq": "configured",
    "state": "ok"
  }
}
```

