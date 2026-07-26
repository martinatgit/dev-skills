# Events and Webhooks

Reference for the eventing model. Load when configuring webhook endpoints, writing a consumer, or debugging missed/duplicated events.

## Table of contents

1. Event object
2. Sources
3. Categories of event_type
4. Webhook delivery semantics
5. Authentication and verification
6. Idempotency and ordering
7. Consumer implementation pattern
8. Failure modes
9. Polling alternative

## 1. Event object

Endpoint: `https://{site}.chargebee.com/api/v2/events`

Reference: <https://apidocs.chargebee.com/docs/api/events>

Fields:
- `id`: max 40 chars. Stable, unique per site. **The de-duplication key**.
- `occurred_at`: Unix seconds UTC.
- `source`: enum (see below).
- `user`: triggering identity. Email for admin/portal, API key name for API, service name for scheduled jobs.
- `event_type`: see categories.
- `api_version`: `v1` or `v2`. Consumer SDK must agree.
- `content`: JSON wrapper containing snapshots of affected resources, e.g. `content.subscription`, `content.customer`, `content.invoice`. Each carries its own `resource_version`.
- `origin_user`: email passed in custom header for API operations (audit trail).
- `webhooks`: array describing delivery status to each configured endpoint.

## 2. Sources

`admin_console`, `api`, `scheduled_job`, `hosted_page`, `portal`, `external_service`, `js_api`, `bulk_operation`, `webhook`.

Use `source` to skip echoing events your own backend caused, when you only want third-party-driven changes.

## 3. Categories of event_type

Grouped by resource. The full canonical list: <https://apidocs.chargebee.com/docs/api/events?prod_cat_ver=2#event_types>

| Group | Examples |
|---|---|
| Customer | `customer_created`, `customer_changed`, `customer_deleted`, `customer_moved_out`, `customer_moved_in` |
| Subscription | `subscription_created`, `subscription_started`, `subscription_activated`, `subscription_changed`, `subscription_cancelled`, `subscription_reactivated`, `subscription_paused`, `subscription_resumed`, `subscription_renewed`, `subscription_renewal_reminder`, `subscription_trial_end_reminder`, `subscription_changes_scheduled`, `subscription_scheduled_changes_removed`, `subscription_cancellation_scheduled`, `subscription_cancellation_scheduled_removed` |
| Payment Source | `payment_source_added`, `payment_source_updated`, `payment_source_deleted`, `payment_source_expiring`, `payment_source_expired` |
| Card | `card_added`, `card_updated`, `card_expired`, `card_expiring`, `card_deleted` |
| Invoice | `invoice_generated`, `invoice_updated`, `invoice_deleted`, `invoice_voided`, `pending_invoice_created`, `pending_invoice_updated` |
| Payment | `payment_succeeded`, `payment_failed`, `payment_initiated`, `payment_refunded`, `refund_initiated` |
| Credit Note | `credit_note_created`, `credit_note_created_with_backdating`, `credit_note_updated`, `credit_note_deleted` |
| Promotional Credits | `promotional_credits_added`, `promotional_credits_deducted` |
| Gift | `gift_scheduled`, `gift_claimed`, `gift_unclaimed`, `gift_cancelled`, `gift_expired`, `gift_updated` |
| Dunning | `dunning_pause`, `dunning_resume`, `dunning_stopped` |
| Item / Item Price (PC 2.0) | `item_created`, `item_updated`, `item_deleted`, `item_price_created`, `item_price_updated`, `item_price_deleted` |
| Plan / Addon (PC 1.0) | `plan_created`, `plan_updated`, `plan_deleted`, `addon_created`, `addon_updated`, `addon_deleted` |
| Quote | `quote_created`, `quote_updated`, `quote_deleted` |
| Hosted Page | `hosted_page_created`, `hosted_page_succeeded`, `hosted_page_requested`, `hosted_page_cancelled`, `hosted_page_acknowledged` |
| Order | `order_created`, `order_updated`, `order_cancelled`, `order_delivered`, `order_returned`, `order_resent` |

## 4. Webhook delivery semantics

- Transport: HTTP POST.
- Content-Type: `application/json`.
- Body: the event object verbatim.
- Retries on non-2XX or timeout: **up to 7 attempts** over ~2 days at fixed offsets after the previous failure: **+2 min, +6 min, +30 min, +1 h, +5 h, +1 d, +2 d**. After the 7th attempt the delivery is abandoned.
- Timeouts (test site / live site):
  - Connection: 10 s / 20 s.
  - Read: 10 s / 20 s.
  - **Total execution: 20 s / 60 s.** The handler must return 2XX inside the total budget; otherwise the call is considered failed and goes into retry.
- **Per-site cap: up to 5 active webhook endpoints.** Plan accordingly when multiplexing consumers; combine via a fan-out service rather than burning multiple endpoints.
- Manual resend: per-event from the Chargebee admin UI.
- Each configured endpoint retries independently.
- No guaranteed ordering across events. Two related events (`invoice_generated` and `payment_succeeded` for the same invoice) may arrive in either order.

Source: <https://www.chargebee.com/docs/2.0/webhook_settings.html>

## 5. Authentication and verification

Two mechanisms, used together is best:

1. **HTTP Basic Auth on the endpoint URL**: configure a username and password (or a random key). Chargebee sends `Authorization: Basic ...`. Reject any request lacking it.
2. **IP allowlist**: Chargebee publishes its outbound IPs at <https://www.chargebee.com/docs/billing/2.0/site-configuration/webhook_settings>. Filter at the load balancer.

There is no HMAC signature on webhooks. To verify a payload is genuine after passing Basic Auth, re-fetch via `GET /events/{id}` and compare. This is the recommended integrity check for sensitive flows.

## 6. Idempotency and ordering

### De-duplication

Persist `event.id` in your own store (e.g. a `processed_events` table with primary key on `event.id` and `processed_at`). Drop any incoming event whose id is already present. Retention window: **3 days 7 hours** (the ~2-day window of the 7-attempt retry schedule from section 4, plus safety margin for clock skew and manual resends).

### Ordering

For each resource id, track the highest `resource_version` you have applied. Skip an incoming event if its `content.<resource>.resource_version` is less than the stored value. This handles late deliveries that would otherwise overwrite newer state.

```python
def should_apply(incoming_rv: int, stored_rv: int | None) -> bool:
    return stored_rv is None or incoming_rv > stored_rv
```

## 7. Consumer implementation pattern

Production-grade handler skeleton:

```python
def chargebee_webhook(request):
    # 1. AuthN at edge (Basic Auth, IP allowlist) is assumed.

    event = request.json
    event_id = event["id"]
    event_type = event["event_type"]
    api_version = event["api_version"]

    if api_version != EXPECTED_API_VERSION:
        log.warn("api_version skew", got=api_version, want=EXPECTED_API_VERSION)
        # Still 200 to stop retries; alert separately.
        return 200

    if already_processed(event_id):
        return 200  # duplicate

    record_pending(event_id)
    enqueue_async_processing(event_id, event_type, event["content"])
    return 200

def process_async(event_id, event_type, content):
    # Idempotently apply state by resource_version.
    if event_type.startswith("subscription_"):
        sub = content["subscription"]
        with transaction():
            row = get_subscription(sub["id"])
            if row and sub["resource_version"] <= row.resource_version:
                return  # stale
            upsert_subscription(sub)
    elif event_type == "payment_failed":
        ...
    mark_processed(event_id)
```

Key properties:
- 2XX returned within the handler timeout (Chargebee retries beyond ~10s; ack fast).
- Heavy work is async (queue, background job).
- All state mutations are idempotent on `event.id` and ordered on `resource_version`.

## 8. Failure modes (and how to spot them)

| Symptom | Probable cause | Fix |
|---|---|---|
| Duplicate side-effects (double-fulfilment) | No de-dupe on `event.id`. | Add `processed_events` table; key on id. |
| State flapping (e.g. subscription appears cancelled then active) | Out-of-order delivery, no resource_version check. | Compare `resource_version`; drop older. |
| Constant retries from Chargebee | Handler returns non-2XX or times out. | Move work async; ack first. Inspect dashboard "Webhooks" page. |
| Missed events | Endpoint Basic Auth misconfigured; firewall blocks Chargebee IPs. | Test from dashboard "Test webhook" button; check IPs. |
| Wrong field shapes | `api_version` mismatch. | Pin SDK; update consumer logic. |
| Events arriving long after the change | Chargebee retried beyond 2 days, or the resource changed via async background job. | Use polling fallback (see below) for time-critical paths. |

## 9. Polling alternative

For time-critical or audit flows, do not depend on webhooks alone. Use the Events API:

- `GET /api/v2/events?limit=100&sort_by[asc]=occurred_at&occurred_at[after]={cursor}`
- Maintain a cursor (`occurred_at`) and resume.
- `GET /api/v2/events/{id}` to re-verify a specific event seen via webhook.

This is also the workaround for the "webhooks aren't recommended for time-critical applications" note in the API docs.
