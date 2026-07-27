# Invoices, Credit Notes, Dunning, Taxes, Proration

Reference for the billing artefacts and revenue-operations machinery. Load when working with invoice state, refunds, taxes, dunning configuration, or proration.

## Table of contents

1. Invoice
2. Credit Note
3. Transaction
4. Dunning
5. Taxes
6. Proration and billing modes
7. Net Terms
8. Consolidated Invoicing
9. Revenue Recognition
10. Webhooks worth handling

## 1. Invoice

Endpoint: `https://{site}.chargebee.com/api/v2/invoices`

Reference: <https://apidocs.chargebee.com/docs/api/invoices>

### Statuses

| Status | Meaning |
|---|---|
| `paid` | Fully collected. |
| `posted` | Issued, not yet due (awaiting collection). |
| `payment_due` | Due, in dunning retry. |
| `not_paid` | Retries exhausted, unpaid, not voided. |
| `voided` | Cancelled. |
| `pending` | Mid-cycle, not yet closed (e.g. metered or pending invoice setting). |

### Key fields

`id`, `customer_id`, `subscription_id` (or `null` for one-off), `status`, `date`, `due_date`, `currency_code`, `sub_total`, `tax`, `total`, `amount_paid`, `amount_due`, `amount_adjusted`, `amount_to_collect`, `credits_applied`, `line_items[]`, `taxes[]`, `linked_payments[]`, `applied_credits[]`, `adjustment_credit_notes[]`, `issued_credit_notes[]`, `resource_version`, `tax_category`, `vat_number`.

### line_items[].entity_type enum (PC 2.0)

Each line item carries `entity_type` (and `entity_id` pointing at that entity). On Product Catalog 2.0 sites, the allowed values are:

| `entity_type` | Source |
|---|---|
| `plan_item_price` | A plan-item-price (recurring subscription core). |
| `addon_item_price` | An addon-item-price (recurring add-on). |
| `charge_item_price` | A charge-item-price (one-time charge driven by a configured Item). |
| `adhoc` | An ad-hoc line item with no Item Price backing (free-form charges, manual invoice lines). |

When filtering for "did the customer buy product X" inside a webhook handler, key off `entity_id` (== the `item_price_id`) plus `entity_type`. On Product Catalog 1.0 sites, the equivalent identifiers are `plan_id` and `addon_id` directly on the line item rather than `entity_type` / `entity_id`.

Source: <https://github.com/chargebee/openapi> (`spec/chargebee_api_v2_pc_v2_spec.yaml`, `entity_type` enum on the invoice `line_items` schema).

### Operations

- `create`: ad-hoc invoice for a customer with `charges[]` and/or `addons[]`.
- `create_for_charge_items_and_charges`: PC 2.0 equivalent.
- `charge` / `charge_addon`: append to a subscription's pending invoice.
- `collect_payment`: force a collection attempt now.
- `refund`: refund a paid invoice; creates a Credit Note and refund Transaction.
- `void`: cancel; only valid for `posted`, `payment_due`, `not_paid`.
- `write_off`: reduce `amount_due` to 0 without payment; emits write-off Credit Note.
- `apply_credits`, `remove_credit_note`: manipulate applied credits.
- `apply_payments`, `remove_payment`: link or unlink existing transactions.
- `stop_dunning`: end retry cycle without changing status.
- `import_invoice`: backfill historic invoices.
- `pdf` / `download` / `send_email`: distribution.

## 2. Credit Note

Endpoint: `https://{site}.chargebee.com/api/v2/credit_notes`

Negative invoice issued for refunds, adjustments, or write-offs.

Types:
- `adjustment`: reduces amount_due on the source invoice.
- `refundable`: refundable credit available on customer's promotional balance or to the original payment source.

Statuses: `adjusted`, `refunded`, `refund_due`, `voided`.

Operations: create, retrieve, list, void, record_refund (offline), refund (online).

Reference: <https://apidocs.chargebee.com/docs/api/credit_notes>

## 3. Transaction

Endpoint: `https://{site}.chargebee.com/api/v2/transactions`

A money movement. One invoice can have many transactions (initial attempt, dunning retries, refunds).

Types: `payment`, `refund`, `authorization`, `payment_reversal`.
Statuses: `success`, `failure`, `voided`, `timeout`, `needs_attention`.

Key fields: `id`, `customer_id`, `subscription_id`, `gateway`, `payment_method`, `reference_number` (gateway-side ref), `amount`, `error_code`, `error_text`.

## 4. Dunning

Configuration: Settings > Configure Chargebee > Dunning, Smart Dunning, Email Notifications v2.

Reference: <https://www.chargebee.com/docs/payments/2.0/dunning/dunning-v2>

### Modes

- **Smart Dunning** (up to 12 retries): Chargebee auto-tunes timing based on the gateway response (soft vs hard decline) and historical patterns. Plan-gated; ask the user if uncertain.
- **Custom Dunning** (up to 5 retries): you provide a day-offset list, e.g. `1,4,8`.
- **Direct Debit**: 1-5 retries; 2 is the recommended default. Settlement takes 5-7 business days.

### Triggers

- `auto_collection=on`.
- An invoice transitions to `payment_due` after the first failed attempt.

### Terminal action (after final retry)

You choose one combination:

Subscription action: `cancel` or `keep_active`.
Invoice action: `not_paid`, `void`, `write_off`, `reverse` (creates a Credit Note with reason `Subscription_Cancellation`).

### Management API

- `POST /invoices/{id}/stop_dunning`: end dunning without changing status.
- `POST /invoices/{id}/collect_payment`: manual retry now.
- Pause / resume dunning: via the UI; API support varies, check current docs.

### 3DS interaction

If the gateway requires SCA, Chargebee schedules a single 3DS retry the day before the dunning period ends. Customers complete it via portal or magic link email.

## 5. Taxes

Configuration: Settings > Configure Chargebee > Taxes.

Reference: <https://www.chargebee.com/docs/billing/2.0/taxes/tax>

Engines supported:
- **Chargebee Tax** (built-in for US sales tax, EU VAT, GB VAT, AU GST, CA, IN GST).
- **Avalara AvaTax**.
- **TaxJar**.
- **Manual tax rates** for unsupported regions.

Pricing modes:
- `tax_exclusive` (default): tax added on top of `sub_total`.
- `tax_inclusive`: tax is contained in the listed price; back-calculated.

Customer-side flags: `taxability` (`taxable`/`exempt`), `vat_number`, `entity_code` (Avalara), `exempt_number`.

Item-side: `tax_profile_id`, `taxable`, `tax_code` (Avalara).

## 6. Proration and billing modes

When mid-term changes happen, decide three things:

1. **Charge timing**: `invoice_immediately` (issue now) or roll into next cycle.
2. **Proration**: `prorate=true` (credit unused time, charge prorated new cost) or `prorate=false` (full new price next cycle, no credit).
3. **Effective date**: `change_option=specific_date|immediately|end_of_term`.

Subscription `update_for_items` parameters:
- `replace_items_list`: bool. If true, the new `subscription_items` array replaces existing items entirely; missing items are removed. If false, it merges by `item_price_id`.
- `billing_alignment_mode`: `delay` or `immediate` (for calendar billing).
- `force_term_reset`: bool. Resets term to today on change (rare).

## 7. Net Terms

`customer.net_term_days`: integer days from invoice issue to due_date. Common: NET 30, NET 60.

Behaviour:
- Invoice issued at status `posted`, due_date `issue_date + net_term_days`.
- Reminders and dunning kick in based on due_date, not issue_date.
- Typically paired with `auto_collection=off` and offline payment recording.

Reference: <https://www.chargebee.com/docs/billing/2.0/subscriptions/net_d>

## 8. Consolidated Invoicing

Groups multiple subscriptions for one customer into a single invoice per billing cycle.

Configuration is per-customer: `customer.consolidated_invoicing=true` and matching `billing_date`. All eligible subscriptions roll up.

Reference: <https://www.chargebee.com/docs/billing/2.0/invoices-credit-notes-and-quotes/consolidated-invoicing>

## 9. Revenue Recognition

Chargebee RevRec aligns billing with ASC 606 / IFRS 15. Deferred revenue schedules are generated per invoice line item. Journal entries can be exported.

API:
- `GET /api/v2/journal_entries`
- `GET /api/v2/deferred_revenue`

Configuration: Settings > Configure Chargebee > Revenue Recognition.

## 10. Webhooks worth handling

- `invoice_generated`, `invoice_updated`
- `invoice_deleted`, `invoice_voided`
- `pending_invoice_created`, `pending_invoice_updated`
- `payment_succeeded`, `payment_failed`, `payment_refunded`, `payment_initiated`
- `refund_initiated`
- `credit_note_created`, `credit_note_created_with_backdating`, `credit_note_updated`, `credit_note_deleted`
- `promotional_credits_added`, `promotional_credits_deducted` (for any flow that grants or deducts a customer's promotional balance)
- `dunning_pause`, `dunning_resume`, `dunning_stopped`
- `subscription_renewal_reminder` (drives pre-renewal UX)
