# Customers, Payment Sources, Payment Intents, 3DS/SCA

Reference for the customer object and the payment plumbing around it. Load when handling signups, payment method updates, 3DS, SCA, or gateway account configuration.

## Table of contents

1. Customer
2. Payment Source
3. Gateway Account
4. Payment Intent and 3DS flow
5. Tokenisation patterns
6. Common operations
7. Webhooks worth handling

## 1. Customer

Endpoint: `https://{site}.chargebee.com/api/v2/customers`

Reference: <https://apidocs.chargebee.com/docs/api/customers>

Key fields:
- `id`: max 50, immutable after creation. Auto-generated if omitted.
- `first_name`, `last_name`, `email`, `phone`, `company`.
- `auto_collection`: `on` (default) or `off`. Off means Chargebee will not attempt to charge automatically; you collect via offline payments or `collect_now`.
- `net_term_days`: integer, used as invoice due_date offset for `auto_collection=off`.
- `taxability`: `taxable` or `exempt`.
- `vat_number`, `entity_code`, `exempt_number`: tax fields.
- `billing_address`: object (line1, city, state, zip, country in ISO 3166-1 alpha-2).
- `payment_method`: legacy single-method block (use Payment Sources for new code).
- `business_entity_id`: assigns to a business entity.
- `customer_type`: `business` or `residential`.
- `cf_*`: custom field columns defined per site.

Primary operations: create, retrieve, list, update, update_payment_method, update_billing_info, collect_now, change_billing_date, move (between business entities), merge, delete, hierarchy operations.

## 2. Payment Source

Endpoint: `https://{site}.chargebee.com/api/v2/payment_sources`

A tokenised instrument attached to a customer. Supersedes the inline `payment_method` block.

Types: `card`, `bank_account`, `boleto`, `direct_debit` (SEPA, BACS, ACH), `paypal`, `apple_pay`, `google_pay`, `amazon_payments`, `venmo`, `ideal`, `sofort`, `bancontact`, and others depending on the gateway.

Statuses: `valid`, `expired`, `expiring`, `invalid`, `pending_verification`.

Key fields:
- `id`, `customer_id`, `gateway_account_id`, `type`, `status`.
- `card`: object with `last4`, `brand`, `expiry_month`, `expiry_year`, `funding_type`, `iin`.
- `reference_id`: the gateway's token/payment-method-id (e.g. Stripe `pm_*`).

Operations: create_using_token, create_using_payment_intent, create_using_permanent_token, retrieve, list, delete, update_card, verify (for direct debit), switch_gateway_account, export_payment_source.

Best practice: create with `payment_intent` (the 3DS-authorised one) for cards; or with `token` from Chargebee.js for non-3DS methods.

## 3. Gateway Account

Endpoint: `https://{site}.chargebee.com/api/v2/gateway_accounts`

A connection to a payment processor. Multiple gateways can coexist; routing is configurable by currency, business entity, and payment method.

Common gateways: Stripe, Adyen, Braintree, Authorize.Net, GoCardless, Spreedly, PayPal Commerce, Razorpay, Worldpay. Full list: <https://www.chargebee.com/docs/payments/2.0/payment-gateways-and-configuration/gateway_settings.html>

Key fields: `id`, `gateway`, `payment_methods` (array), `currencies` (array), `business_entity_id`.

## 4. Payment Intent and 3DS flow

Endpoint: `https://{site}.chargebee.com/api/v2/payment_intents`

Used to satisfy 3DS / SCA. A payment intent is a one-shot artefact that authorises an amount on a customer's card, then is consumed by a subscription, invoice, or order.

Statuses:
- `inited`: created, awaiting front-end interaction.
- `in_progress`: 3DS challenge in flight.
- `authorized`: 3DS cleared, intent ready to consume.
- `consumed`: used in an API call (cannot be reused).
- `expired`: not consumed within 1 hour.

Reference: <https://apidocs.chargebee.com/docs/api/payment_intents>

### Standard server-orchestrated 3DS flow

1. **Server creates intent**:
   ```bash
   POST /api/v2/payment_intents
   amount=2995
   currency_code=EUR
   gateway_account_id=gw_stripe_eu
   payment_method_type=card
   reference_id=pm_stripe_xxx   # optional, if already tokenised
   ```
   Returns `payment_intent.id` and `gateway_meta_data` to feed to Chargebee.js.

2. **Client completes 3DS** via `chargebee.handleCardPayment(intent)` or the Drop-In's built-in handler. Result is the same intent now in `authorized` state.

3. **Server consumes** by passing `payment_intent[id]=...` on the next mutation:
   - `POST /subscriptions` (new subscription)
   - `POST /subscriptions/{id}/update_for_items`
   - `POST /invoices` (charge)
   - `POST /payment_sources` with `create_using_payment_intent`

4. **Server verifies** result: response will include the resulting subscription/invoice. The intent is now `consumed`.

### Retry semantics

If the intent expires or is declined, create a new intent. Do not retry the same intent id.

### Dunning interaction

For renewal-time 3DS failures, Chargebee schedules a single 3DS retry the day before dunning ends; the customer must complete it via portal or a magic link.

## 5. Tokenisation patterns

Never accept card numbers on your backend. Choose one of:

1. **Chargebee.js Drop-In**: managed checkout, you get a `payment_intent` or `hosted_page_id` callback.
2. **Chargebee.js Components**: your form, Chargebee fields. Call `chargebee.tokenize()` to get a token, then `create_using_token`.
3. **Gateway-native token**: the gateway (e.g. Stripe) issues `pm_*`. Pass it as `tmp_token` to `payment_sources/create_using_token` and Chargebee stores the reference.

See `references/hosted_chargebeejs.md`.

## 6. Common operations

| Goal | Endpoint |
|---|---|
| Add a new card to a customer | `POST /payment_sources/create_using_payment_intent` |
| Replace primary card | `POST /customers/{id}/update_payment_method` |
| Update billing address | `POST /customers/{id}/update_billing_info` |
| Charge an unpaid invoice now | `POST /customers/{id}/collect_now` |
| Move customer between entities | `POST /customers/{id}/move` |
| Merge duplicates | `POST /customers/merge` |

## 7. Webhooks worth handling

- `customer_created`, `customer_changed`, `customer_deleted`
- `payment_source_added`, `payment_source_updated`, `payment_source_deleted`
- `payment_source_expiring`, `payment_source_expired`
- `payment_succeeded`, `payment_failed`, `payment_initiated`, `payment_refunded`
- `card_expiring`, `card_expired`, `card_added`, `card_updated`, `card_deleted`
- `payment_intent_created`, `payment_intent_updated`
