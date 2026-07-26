# Product Catalog

Reference for the Chargebee Product Catalog, both 2.0 (current) and 1.0 (legacy). Load when modelling SKUs, prices, or migrating between versions.

## Table of contents

1. Which version are we on?
2. Product Catalog 2.0 object graph
3. Item
4. Item Price
5. Item Family
6. Attached Item
7. Differential Pricing
8. Price models
9. Metered and usage-based billing
10. Product Catalog 1.0 (legacy)
11. Migration 1.0 -> 2.0

## 1. Which version are we on?

A site is bound to one Product Catalog version. Detect:
- 2.0 endpoint exists: `GET /api/v2/items` returns 200 with a `list`.
- 1.0 endpoint exists: `GET /api/v2/plans` returns 200 with a `list`.
- If a site is on 2.0, calling 1.0 endpoints returns 404 or a deprecation error.

If unknown, ask the user. Do not branch on guesses.

Docs: <https://www.chargebee.com/docs/billing/2.0/product-catalog/product-catalog-versions.html>

## 2. Product Catalog 2.0 object graph

```
Item Family
  └── Item (type=plan | addon | charge)
        ├── Item Price (currency, period, price model)
        ├── Attached Item (auto-bundled item id)
        └── Differential Price (override for a plan combo)
```

Subscription -> Subscription Items -> Item Price (not Item directly).
Invoice Line Item -> Item Price (or Charge).

## 3. Item

Endpoint: `https://{site}.chargebee.com/api/v2/items`

Key fields:
- `id` (max 100), immutable. Use a stable slug, e.g. `pro-plan`.
- `name` (max 100), display only.
- `type`: `plan`, `addon`, `charge`.
- `item_family_id`.
- `status`: `active`, `archived`, `deleted`.
- `is_shippable`: boolean for physical goods.
- `enabled_in_portal`: whether self-serve portal can switch to it.
- `metered`: boolean. If true, quantity comes from usage records, not subscription input.
- `usage_calculation`: `sum_of_usages`, `last_usage`, `max_usage`. Applies when `metered=true`.
- `archived_at`: timestamp.

Operations: create, retrieve, update, list, delete, copy.

Source: <https://apidocs.chargebee.com/docs/api/items>

## 4. Item Price

Endpoint: `https://{site}.chargebee.com/api/v2/item_prices`

A specific monetisation of an item. One item commonly has many item_prices:
- per currency (USD monthly, EUR monthly, USD yearly).
- per geography.
- per pricing tier.

Key fields:
- `id` (max 100). Convention: `<item-id>-<period>-<currency>` e.g. `pro-plan-monthly-usd`.
- `item_id`.
- `currency_code`.
- `period`, `period_unit` (`day`, `week`, `month`, `year`).
- `price` (minor units) or `tiers` for tiered/volume/stairstep.
- `pricing_model`: `flat_fee`, `per_unit`, `tiered`, `volume`, `stairstep`, `unlimited`.
- `free_quantity`: included quantity at no extra cost.
- `trial_period`, `trial_period_unit`: per-price trial override.
- `invoice_notes`: free text added to invoice line item.

Operations: create, update, retrieve, list, delete.

Source: <https://apidocs.chargebee.com/docs/api/item_prices>

### Item Price -> invoice line item linkage

When an Item Price is billed, the resulting invoice line item carries `entity_id = <item_price_id>` and `entity_type` set to one of `plan_item_price`, `addon_item_price`, or `charge_item_price`, matching the parent Item's `type`. Ad-hoc lines without an Item Price backing use `entity_type = adhoc`. See `invoices_billing.md` §1 for the full enum. Webhook consumers should filter on this pair to recognise which Item triggered the line.

## 5. Item Family

Endpoint: `https://{site}.chargebee.com/api/v2/item_families`

Organisational unit. Items belong to exactly one family. Useful when modelling multiple product lines on one site, or for permission scoping.

Key fields: `id`, `name`, `description`, `status`.

## 6. Attached Item

Endpoint: `https://{site}.chargebee.com/api/v2/items/{item_id}/attached_items`

Defines that when a customer subscribes to plan `A`, addon `X` is added by default. Configurable as:
- `type`: `recommended`, `mandatory`, `optional`.
- `charge_on_event`: `subscription_creation`, `subscription_trial_start`, `plan_activation`, `subscription_activation`, `contract_termination`.
- `charge_once`: boolean.

## 7. Differential Pricing

Endpoint: `https://{site}.chargebee.com/api/v2/item_prices/{item_price_id}/differential_pricing`

Override an addon's price when paired with a specific plan-item. Common for tier-based discounting where the same addon costs less on Enterprise than on Pro.

## 8. Price models

Choose the model when creating an item_price. Cannot be changed in-place; create a new item_price instead.

| Model | Description | Example |
|---|---|---|
| `flat_fee` | Fixed amount per cycle, ignores quantity. | $99/month for the seat-unlimited plan. |
| `per_unit` | `price * quantity`. | $10 per seat. |
| `tiered` | Each unit billed at its tier's rate, summed. | 1-10 at $10 each, 11+ at $8 each. |
| `volume` | All units billed at the rate matching total quantity. | 1-10 -> $10/unit; 11+ -> $8/unit, all units repriced. |
| `stairstep` | Price is a step function of quantity package. | $50 for 1-10, $80 for 11-25. |
| `unlimited` | No quantity multiplier; flat per cycle. | Used with feature-based metering. |

Tier shape:
```json
"tiers": [
  { "starting_unit": 1,  "ending_unit": 10, "price": 1000 },
  { "starting_unit": 11, "price": 800 }
]
```

## 9. Metered and usage-based billing

Enable by setting `metered=true` on the item and choosing a `usage_calculation`.

Flow:
1. Create item with `metered=true`.
2. Customer subscribes; subscription created with quantity 0 (or initial).
3. During the term, record usage via the **Usages** API: `POST /api/v2/subscriptions/{id}/usages` with `quantity`, `usage_date`, optional `dedupe_option`.
4. At term end, Chargebee aggregates usage according to `usage_calculation` and bills the resulting quantity at the item_price's pricing model.

For real-time control, query `GET /api/v2/subscriptions/{id}/usages` to inspect recorded usage.

Source: <https://www.chargebee.com/docs/billing/2.0/usage-based-billing/metered_billing.html>

## 10. Product Catalog 1.0 (legacy)

Endpoints:
- `https://{site}.chargebee.com/api/v2/plans`
- `https://{site}.chargebee.com/api/v2/addons`
- `https://{site}.chargebee.com/api/v2/coupons`

Differences from 2.0:
- No item/item_price split: a Plan combines identity and price.
- One currency per plan; for multi-currency you create separate plans.
- Subscription holds `plan_id` directly, plus `addons` array.
- Metered handled per-plan via `meter`.

Do not start new integrations on 1.0. Maintain only.

## 11. Migration 1.0 -> 2.0

Migration is per-site and irreversible. High-level steps:

1. Audit current plans, addons, charges, coupons. Build a mapping table to Items and Item Prices.
2. Request migration from Chargebee Support (gated process).
3. After migration, all existing subscriptions are auto-rewritten to reference item_prices. Their `plan_id` is preserved as the migrated item_price's `id`.
4. Update client code to use `subscription_items` instead of `plan_id` / `addons` parameters on subscription create and update.
5. Re-run end-to-end smoke tests on the test site before promoting.

Watch for:
- Webhook payload `api_version`: still emits per the configured version; consumer must agree.
- SDK version: must support 2.0 endpoints; older SDKs will not.
- Coupons in 2.0: same endpoint, but applies via `coupon_ids` on subscriptions.
