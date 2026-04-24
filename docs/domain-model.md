# Domain Model

## Entities

### Family

Represents one parent-child household context for the MVP.

Fields:

- `id`
- `name`
- `parent_user_id`
- `kid_user_id`
- `parent_monetary_account_id`
- `kid_monetary_account_id`

### User

Represents either the parent or the kid.

Fields:

- `id`
- `role`: `parent` or `kid`
- `display_name`

### Gig

Represents a household task that can earn money.

Fields:

- `id`
- `family_id`
- `title`
- `description`
- `reward_amount`
- `currency`
- `status`
- `created_by_user_id`
- `claimed_by_user_id`
- `verification_checklist`
- `before_photo_id`
- `after_photo_id`
- `verification_result_id`
- `payment_id`
- `created_at`
- `updated_at`

Statuses:

- `open`
- `claimed`
- `awaiting_after_photo`
- `verifying`
- `approved`
- `paid`
- `rejected`
- `payment_failed`

### Photo

Represents a before or after image submitted for a gig.

Fields:

- `id`
- `gig_id`
- `kind`: `before` or `after`
- `content_type`
- `storage_ref`
- `created_at`

MVP storage uses files under `data/uploads/`, with JSON storing only references. The API may accept base64 for implementation speed, but local state should not store full image payloads.

### Verification Result

Represents Claude Vision's comparison result.

Fields:

- `id`
- `gig_id`
- `approved`
- `confidence`
- `tags`
- `message_for_kid`
- `reasoning_summary`
- `raw_provider`
- `raw_model`
- `created_at`

### Payment

Represents the bunq transfer created after approval.

Fields:

- `id`
- `gig_id`
- `amount`
- `currency`
- `from_monetary_account_id`
- `to_monetary_account_id`
- `bunq_payment_id`
- `status`
- `created_at`
- `updated_at`

Statuses:

- `pending`
- `succeeded`
- `failed`

## Gig State Flow

```text
open
  -> claimed
  -> awaiting_after_photo
  -> verifying
  -> approved
  -> paid
```

Failure paths:

```text
verifying -> rejected
approved -> payment_failed
```

Recovery rules:

- A `rejected` gig can accept a new after photo.
- A `payment_failed` gig can retry payment without re-running AI verification.
- A `verifying` gig should not accept duplicate completion requests unless the request is idempotent.

## Core Invariants

- A gig cannot be paid unless verification is approved.
- A gig cannot be paid more than once.
- A payment must be tied to exactly one gig.
- A kid balance shown after completion should come from bunq when available, not only local state.
- Local fallback state must clearly mark simulated values if bunq is unavailable.
