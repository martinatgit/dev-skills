# Subscriptions

Reference for the subscription object, lifecycle, and operations. Load when creating, modifying, pausing, resuming, or cancelling subscriptions.

## Table of contents

1. Endpoint
2. Object schema
3. Status state machine
4. Create flows
5. Update / change flows
6. Pause / resume
7. Cancel / reactivate
8. Scheduled changes
9. Edge cases
10. Webhooks worth handling

## 1. Endpoint

Base: `https://{site}.chargebee.com/api/v2/subscriptions`

Reference: <https://apidocs.chargebee.com/docs/api/subscriptions>

## 2. Object schema (Product Catalog 2.0)

Key fields:
- `id`: stable, max 50 chars. Auto-generated if omitted.
- `customer_id`: required.
- `currency_code`: ISO 4217.
- `status`: see state machine.
- `billing_period`, `billing_period_unit`: derived from the primary plan-item-price.
- `start_date`, `trial_end`, `current_term_start`, `current_term_end`, `next_billing_at`.
- `subscription_items`: array of `{ item_price_id, quantity, unit_price?, billing_cycles?, trial_end?, service_period_days?, item_type }`.
- `coupon_ids`: applied coupons.
- `cancelled_at`, `cancel_reason`, `cancelled_at`, `cancel_schedule_created_at`.
- `pause_date`, `resume_date`.
- `auto_collection`: inherits from customer unless overridden.
- `business_entity_id`.
- `resource_version`: millisecond timestamp; use for webhook ordering.

Constraint: max 900 subscriptions per customer (active + inactive).

## 3. Status state machine

```
                    +---------+
       create  ---> | future  |
                    +----+----+
                         |
                         | (start_date reached, has trial)
                         v
                    +----+----+
                    | in_trial|
                    +----+----+
                         |
                         | (trial_end)
                         v
                    +----+----+        cancel (schedule)        +-------------+
      create  ---> | active  | -----------------------------> | non_renewing|
                    +----+----+                                +------+------+
                       |  |  \                                        |
                pause  |  |   \cancel (immediate)                     | (term_end)
                       v  |    \                                      v
                  +----+--+-+   ----> +----------+                +---------+
                  | paused | -------> | cancelled| <------------- |cancelled|
                  +-----+--+ resume   +----+-----+    auto        +---------+
                                            ^
                                            | reactivate (within window)
                                            |
                                       +----+-----+
                                       | active   |
                                       +----------+
```

`transferred` is reachable only via business entity move operations.

## 4. Create flows

### Direct create (server-side, customer already exists)

```bash
POST /api/v2/subscriptions
customer_id=cust_123
subscription_items[item_price_id][0]=basic-monthly-usd
subscription_items[quantity][0]=1
coupon_ids[0]=WELCOME10
chargebee-idempotency-key: <uuid>
```

### Create with new customer

```bash
POST /api/v2/customers/{id}/subscription_for_items
subscription_items[item_price_id][0]=basic-monthly-usd
```

Use this when the customer exists but you want to add a new subscription.

### Create from hosted checkout

```bash
POST /api/v2/hosted_pages/checkout_new_for_items
subscription_items[item_price_id][0]=basic-monthly-usd
customer[email]=alice@example.com
embed=false
```

Returns a `hosted_page.url`. Redirect or load via Chargebee.js.

### Create with 3DS payment intent

```bash
POST /api/v2/subscriptions
customer_id=cust_123
subscription_items[item_price_id][0]=pro-monthly-eur
payment_intent[id]=pi_xxx_authorised_via_chargebeejs
```

See `references/customers_payment.md` for the 3DS flow that produces the intent.

## 5. Update / change flows

Mid-term change to subscription items, quantity, addons, or coupons:

```bash
POST /api/v2/subscriptions/{id}/update_for_items
subscription_items[item_price_id][0]=pro-monthly-usd
subscription_items[quantity][0]=5
replace_items_list=true
prorate=true
end_of_term=false
invoice_immediately=true
chargebee-idempotency-key: <uuid>
```

Decision points:
- `prorate=true`: charges the unused-time credit and prorated new cost on the change date.
- `prorate=false`: ignores credit; charges full new price at next cycle.
- `end_of_term=true`: defers the change to term end. Creates a Scheduled Change.
- `replace_items_list=true`: full replacement of `subscription_items`. Default is partial merge.
- `invoice_immediately=true`: forces issue of an invoice now rather than waiting for the cycle.

## 6. Pause / resume

Pause:
```bash
POST /api/v2/subscriptions/{id}/pause
pause_option=immediately   # or specific_date | end_of_term
unbilled_charges_handling=invoice  # or no_action
```

Resume:
```bash
POST /api/v2/subscriptions/{id}/resume
resume_option=immediately  # or specific_date
charges_handling=invoice_immediately
```

While paused: no billing, no usage accrual unless the item is configured to accrue during pause.

## 7. Cancel / reactivate

Cancel immediately:
```bash
POST /api/v2/subscriptions/{id}/cancel_for_items
end_of_term=false
credit_option_type=prorated   # or full | none
refundable_credits_handling=schedule_refund
```

Cancel at term end (scheduled):
```bash
POST /api/v2/subscriptions/{id}/cancel_for_items
end_of_term=true
```
Subscription moves to `non_renewing`. To undo: `POST /subscriptions/{id}/remove_scheduled_cancellation`.

Reactivate cancelled:
```bash
POST /api/v2/subscriptions/{id}/reactivate
trial_end=0
```
Only possible within the retention window. After purge it must be recreated.

## 8. Scheduled changes

Many operations support `end_of_term=true` to defer. Inspect pending changes via:
```
GET /api/v2/subscriptions/{id}/retrieve_with_scheduled_changes
```

Remove all scheduled changes:
```
POST /api/v2/subscriptions/{id}/remove_scheduled_changes
```

## 9. Edge cases

- **Trial overrides**: per-subscription `trial_end` beats per-item_price trial.
- **Free subscription** (price 0): still goes through invoice generation but with `total=0`; no payment is attempted.
- **Subscription with multiple plan-items**: not supported. A subscription has exactly one plan-item; the rest must be addons or charges.
- **Quantity 0 on metered**: valid; quantity is computed from usage records at term end.
- **Currency mismatch**: subscription currency must match the customer's first transaction currency on most gateways. Multi-currency gateways differ.
- **Time zone**: `current_term_end` is exclusive in some integrations; treat it as the renewal moment, not the last billed second.

## 10. Webhooks worth handling

Subscribe to and idempotently apply these event types:

- `subscription_created`
- `subscription_started` (after `future` becomes `active`)
- `subscription_activated` (after trial -> active)
- `subscription_trial_end_reminder`
- `subscription_changed`
- `subscription_changes_scheduled` / `subscription_scheduled_changes_removed`
- `subscription_cancellation_scheduled` / `subscription_cancellation_scheduled_removed`
- `subscription_cancelled`
- `subscription_reactivated`
- `subscription_paused`
- `subscription_resumed`
- `subscription_renewed`
- `subscription_renewal_reminder`

A complete list: <https://apidocs.chargebee.com/docs/api/events?prod_cat_ver=2#event_types>
