# Chargebee API Fundamentals

Reference for API mechanics. Load when implementing any direct HTTP call or auditing SDK behaviour.

## Base URL and environments

- Pattern: `https://{site}.chargebee.com/api/v2/`
- `{site}` is the tenant subdomain. Test site and live site have different subdomains and different API keys.
- The site domain encodes the data centre (US, EU, AU). Latency-sensitive callers should colocate.

Source: <https://apidocs.chargebee.com/docs/api/getting-started>

## Authentication

- Scheme: HTTP Basic Auth.
- Username: the API key (Full-Access or Read-Only).
- Password: empty string.

Example:
```bash
curl https://acme-test.chargebee.com/api/v2/customers \
  -u live_xxxxxxxxxxxxxx:
```

API key types:
- **Full-Access Key**: read + write across all resources.
- **Read-Only Key**: list/retrieve only.
- **App-specific Key**: scoped to a registered application; recommended for partner apps.

Rotate keys via the Chargebee UI. Keys cannot be recovered after creation, only regenerated.

## Request format

- Method: `POST` for create/update/delete, `GET` for read.
- Content-Type for `POST`: `application/x-www-form-urlencoded`.
- Nested fields use bracket syntax: `customer[email]=alice@example.com&billing_address[city]=Berlin`.
- Array fields use indexed bracket syntax: `subscription_items[item_price_id][0]=basic-monthly&subscription_items[quantity][0]=1`.

## Response format

- Always JSON.
- Single resource: `{ "customer": { ... } }`.
- List: `{ "list": [ { "customer": { ... } }, ... ], "next_offset": "[\"...\"]" }`.
- Compound responses include all linked resources, e.g. `subscription`, `customer`, `invoice`, `card`.

## Pagination

- Parameter: `limit` (default 10, max 100).
- Parameter: `offset` (opaque cursor returned as `next_offset` from the previous page).
- Stop when `next_offset` is absent.
- Filtering uses `<field>[operator]=value`, e.g. `created_at[after]=1700000000`, `status[is]=active`, `status[in]=["active","in_trial"]`.

## Idempotency

Send the header `chargebee-idempotency-key` on any `POST` that creates or mutates state. Required for safe retries.

- Format: UUIDv4 (recommended) or any random string up to 100 characters.
- Scope: one logical operation = one key. Do not reuse across operations.
- On replay: Chargebee returns the cached response and sets the response header `chargebee-idempotency-replayed: true`. The body is byte-identical to the original.
- Estimate APIs do not support idempotency. Do not send the header for those endpoints.

```bash
curl -X POST https://acme-test.chargebee.com/api/v2/subscriptions \
  -u live_xxxxxxxxxxxxxx: \
  -H "chargebee-idempotency-key: 4b4f8f0e-d2b8-4b3b-9b0f-9a1b6e2c0d11" \
  -d "subscription_items[item_price_id][0]=basic-monthly"
```

Source: <https://apidocs.chargebee.com/docs/api/idempotency?prod_cat_ver=2>

## Rate limiting

- HTTP 429 indicates throttling.
- No documented header schema for retry-after; back off with exponential delay (e.g. 1s, 2s, 4s, 8s) capped at the deadline of the calling operation.
- Bulk operations have separate concurrency limits; use the Bulk Operations API rather than tight loops.

## Errors

Error response shape:
```json
{
  "message": "Invalid Operation",
  "type": "invalid_request",
  "api_error_code": "param_wrong_value",
  "error_code": "param_wrong_value",
  "http_status_code": 400,
  "param": "subscription_items[item_price_id][0]"
}
```

Important fields:
- `api_error_code`: stable machine-readable identifier; switch on this.
- `param`: the offending field, if any.
- `type`: `invalid_request`, `payment`, `operation_failed`, `io_error`.

Categories of HTTP status:
- 400: validation, business rule violation.
- 401: bad or missing API key.
- 404: resource not found.
- 409: state conflict.
- 429: rate limit.
- 5xx: server error, retry-safe with idempotency key.

## Time and money formats

- Timestamps: Unix epoch seconds. UTC.
- Money: integer minor units in `currency_code` (e.g. cents for USD). `amount=1995` means USD 19.95.
- Quantities: integer or decimal depending on the item configuration.

## SDKs

Official libraries (use these rather than raw HTTP when possible):
- Node: <https://github.com/chargebee/chargebee-node>
- Python: <https://github.com/chargebee/chargebee-python>
- PHP: <https://github.com/chargebee/chargebee-php>
- Java: <https://github.com/chargebee/chargebee-java>
- Go: <https://github.com/chargebee/chargebee-go>
- Ruby: <https://github.com/chargebee/chargebee-ruby>
- .NET: <https://github.com/chargebee/chargebee-dotnet>
- Laravel adapter: provided in Chargebee samples.
- Next.js adapter: provided in Chargebee samples.

OpenAPI spec: <https://github.com/chargebee/openapi> (OpenAPI 3.0.1).

When a binding lags the API, fall back to raw HTTP and document the version skew.

## API version pinning

- Each event payload carries `api_version` (`v1` or `v2`). Webhook consumers must verify this matches the SDK version in use, otherwise field names and shapes may differ.
- The site has a default API version. Per-call override is not supported on the request; pin via the site setting and your SDK version.

## API Explorer and changelog

- Live request builder: <https://api-explorer.chargebee.com/>
- Changelog: <https://www.chargebee.com/help/api-updates/>

Check the changelog before adopting a new SDK major version. Breaking changes are gated by version.
