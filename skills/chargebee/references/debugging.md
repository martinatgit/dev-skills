# Debugging Chargebee Integrations

Triage playbooks for the common failure modes. Load when the user reports a Chargebee error, an unexpected state, or a missing webhook.

## Universal first steps

Before any deep dive, collect:

1. **Site**: live or test? `{site}` value.
2. **Request**: method, URL, full headers (mask the API key), body. Reproduce with curl or the API Explorer.
3. **Response**: HTTP status, `api_error_code`, `error_code`, `type`, `message`, `param`.
4. **Idempotency context**: was `chargebee-idempotency-key` sent? Is the response a replay (`chargebee-idempotency-replayed: true`)?
5. **Time**: when did it fail? Cross-check the Chargebee site's audit log and the gateway dashboard.
6. **Resource**: id of the customer/subscription/invoice/event involved. Open it in the Chargebee admin UI for ground truth.

Useful tools:
- API Explorer: <https://api-explorer.chargebee.com/>
- Audit log: Chargebee admin > Settings > Audit Logs
- Webhooks log: Chargebee admin > Settings > Webhooks > recent deliveries
- Gateway dashboard (Stripe, Adyen, etc.) for payment-level errors.
- Changelog: <https://www.chargebee.com/help/api-updates/> to rule out version skew.

## Error catalogue (most common `api_error_code` values)

| `api_error_code` | Meaning | Typical fix |
|---|---|---|
| `param_wrong_value` | A field has an invalid value. | Check `param` in response; consult API ref for allowed values. |
| `param_not_provided` | Required field missing. | Add field; verify SDK serialiser. |
| `param_invalid_format` | Wrong format (e.g. id too long, email malformed). | Fix client validation. |
| `invalid_state_for_request` | Operation not valid in current resource state. | E.g. cannot cancel a `cancelled` sub. Check status first. |
| `resource_not_found` | id mismatch or wrong site. | Verify the `{site}` and id. |
| `duplicate_entry` | id collision (e.g. customer.id already exists). | Use new id or omit to auto-generate. |
| `payment_processing_failed` | Gateway-side decline. | Read `error_code`/`error_text` from the linked transaction. |
| `api_authentication_failed` | Bad API key. | Check key environment (test vs live). |
| `api_authorization_failed` | Key lacks permission. | Use Full-Access for write; check app scopes. |
| `api_request_limit_exceeded` | 429 throttle. | Backoff exponentially; reduce concurrency. |
| `internal_error` | 5xx server. | Retry with idempotency key; if persistent, file a ticket. |

Full list: <https://apidocs.chargebee.com/docs/api/errors>

## Playbook: webhook not received

1. Open Chargebee admin > Settings > Webhooks. Find the event in the recent deliveries log.
2. Status?
   - **Success**: your endpoint returned 2XX. Check your downstream processing; perhaps de-dup dropped it.
   - **Failure**: read response code and body. Common: 401 (Basic Auth misconfigured on your side), 403 (IP block), 504 (timeout, your handler too slow), 5xx (your app errored).
3. If status is "in retry": wait or use "Resend" to test fixes. Chargebee retries for up to 2 days.
4. If the event never appears: confirm the endpoint is **enabled for the relevant event types** under the webhook's configuration.
5. Test from the admin UI's "Test webhook" button to verify connectivity isolated from the event source.

## Playbook: duplicate side-effect after webhook

Cause: no idempotent storage on `event.id`.

Fix:
- Create `processed_events(event_id PRIMARY KEY, processed_at)`.
- On every webhook, `INSERT ... ON CONFLICT DO NOTHING`; bail if it was already there.
- Retention: at least 4 days (Chargebee's 2-day retry plus margin).

## Playbook: state-flapping (e.g. subscription appears cancelled then active)

Cause: out-of-order webhook delivery without `resource_version` ordering.

Fix:
- Persist `subscription.resource_version` per id.
- On incoming event, ignore if `content.subscription.resource_version <= stored`.
- For the missed transition, re-fetch via `GET /subscriptions/{id}` after settle.

## Playbook: 3DS challenge succeeded on client but server rejects intent

Symptoms: `payment_intent.id` consume returns `payment_processing_failed` or `invalid_state_for_request`.

Causes and fixes:
- Intent in `consumed` state (already used). Create a new one.
- Intent expired (>1 hour). Create a new one.
- Wrong `gateway_account_id` (e.g. EU customer routed to a US gateway). Pass the explicit `gateway_account_id` matching customer currency and entity.
- Currency mismatch: intent currency must equal subscription currency.

## Playbook: dunning never triggers

Causes:
- `customer.auto_collection=off`. Chargebee will not auto-charge; dunning does not apply.
- Customer has no valid payment_source.
- Dunning configuration disabled or maximum retries set to 0.

Validate: trigger a failed transaction manually with the Test Gateway's failure cards, then check the invoice status path.

## Playbook: proration not as expected after a plan change

Diagnostic order:
1. Was `prorate=true`?
2. Was the change applied immediately (`change_option=immediately` is the default for `update_for_items`) or `end_of_term`?
3. Is the item_price `pricing_model=flat_fee`? Flat fees compute proration by elapsed/total cycle time, not by quantity.
4. For tiered/volume/stairstep, proration uses the new tier rate prorated by remaining days.
5. Check the resulting invoice line items for `prorated_taxable_amount` and `prorated_unit_amount`.

Use the **Estimate API** to preview before applying:
```
POST /estimates/update_subscription_for_items
```

## Playbook: live vs test confusion

Symptoms: "It works in dev but customers report it doesn't."

Checks:
- `CHARGEBEE_SITE` env var: ends with `-test` for sandbox, no suffix or `-live` convention for prod.
- API key prefix: differs by environment.
- Webhook endpoints: configured per site; ensure prod endpoint is set on the live site.
- MCP server URL: `https://{site}.mcp.chargebee.com/...` mirrors the site, not the company.

## Playbook: SDK behaviour differs from API docs

Causes:
- SDK is older than the documented API. Check version; pin to the changelog entry that introduced the field.
- Field requires PC 2.0 but site is on PC 1.0 (or vice versa).
- Field is gated behind a paid Chargebee plan tier.

Resolution path: fall back to raw HTTP with curl/API Explorer to confirm the server accepts the field, then either upgrade the SDK or call HTTP directly.

## Playbook: rate limited (429)

1. Identify which endpoint is hot. Tag log lines with the endpoint family.
2. Batch where possible (List with filters instead of N retrieve calls).
3. Use the Bulk Operations API for backfill: <https://apidocs.chargebee.com/docs/api/bulk_operations>
4. Add exponential backoff with full jitter on the client.
5. Avoid tight webhook re-processing loops; persist events and process in a queue with a worker pool.

## When to escalate

Open a Chargebee support ticket with these in hand:
- Site name and environment.
- `event.id` and `event_type`, or full request id (`X-Request-Id` if returned).
- Timestamps in UTC.
- Reproduction steps from the API Explorer.

Support entry: <https://www.chargebee.com/docs/billing/2.0/kb/getting-started/how-to-contact-chargebees-support-team>
