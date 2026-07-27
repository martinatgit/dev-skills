# Entitlements and Features

Reference for decoupling feature gating from billing. Load when building feature flags driven by plan, enforcing quotas, or implementing trial-to-paid upgrades that unlock capabilities.

## Table of contents

1. Why entitlements
2. Object model
3. Feature types
4. API endpoints
5. Consumer pattern
6. Worked example

## 1. Why entitlements

Anti-pattern: product code reads `subscription.plan_id == "pro"`. Result: every pricing experiment requires a deploy; sales-led overrides require code branches; sunset plans haunt the codebase.

Pattern: product code reads `entitlements["api_calls_per_month"]` against the customer's current entitlements snapshot. Pricing changes happen in Chargebee; code is stable.

Reference: <https://www.chargebee.com/docs/billing/2.0/entitlements/entitlements>

## 2. Object model

```
Feature
  id, name, type, status, levels[]
        |
        | (entitled by)
        v
Item Entitlement
  item_id (plan or addon), feature_id, value
```

A subscription's effective entitlements are computed by merging the entitlements of all its plan-item and addon-items at evaluation time.

## 3. Feature types

- **Switch**: boolean. The feature is on or off for the plan. Example: `sso_enabled`.
- **Quantity**: integer cap. Example: `seats_max=25`.
- **Range**: bounded numeric, often with levels. Example: `api_calls_per_month=10000`.
- **Custom**: free-form enum or string. Example: `support_tier=priority`.

Each feature can define **levels** (named values with display labels), useful for UI tier badges.

Sources for type detail: <https://www.chargebee.com/docs/billing/2.0/entitlements/features-overview>

## 4. API endpoints

- `GET /api/v2/features` — list defined features.
- `POST /api/v2/features` — create a feature.
- `GET /api/v2/features/{id}` — retrieve.
- `POST /api/v2/items/{id}/item_entitlements` — set entitlements for an item.
- `GET /api/v2/items/{id}/item_entitlements` — list.
- `GET /api/v2/subscriptions/{id}/subscription_entitlements` — effective entitlements for a subscription (the API most product code calls).
- `POST /api/v2/subscriptions/{id}/subscription_entitlements` — override per subscription (sales-led grants).

API reference: <https://apidocs.chargebee.com/docs/api/features>

## 5. Consumer pattern

Cache aggressively. Entitlements rarely change mid-term. Recommended:

1. On `subscription_created`, `subscription_changed`, `subscription_renewed`, `subscription_cancelled` events, refresh the customer's entitlements snapshot in your store.
2. Hot path reads from your store, not Chargebee.
3. TTL fallback (e.g. 1 hour) refreshes via `GET /subscriptions/{id}/subscription_entitlements`.

```python
def can_do(customer_id, feature_id) -> bool:
    ent = entitlements_for(customer_id)  # local cache
    return ent.get(feature_id) is not None and ent[feature_id] != "off"

def remaining_quota(customer_id, feature_id) -> int:
    ent = entitlements_for(customer_id)
    cap = ent.get(feature_id, 0)
    used = usage_for(customer_id, feature_id)
    return max(0, cap - used)
```

## 6. Worked example

Goal: a SaaS with three plans (Starter, Pro, Enterprise) gating `seats`, `api_calls_per_month`, `sso_enabled`.

1. Create features:
   ```bash
   POST /features id=seats name="Seats" type=quantity
   POST /features id=api_calls_per_month name="API calls / month" type=range
   POST /features id=sso_enabled name="SSO" type=switch
   ```
2. Attach entitlements to plan-items:
   ```bash
   POST /items/starter-plan/item_entitlements
     entitlements[feature_id][0]=seats             entitlements[value][0]=3
     entitlements[feature_id][1]=api_calls_per_month entitlements[value][1]=1000
     entitlements[feature_id][2]=sso_enabled       entitlements[value][2]=off
   POST /items/pro-plan/item_entitlements
     ... seats=25, api_calls_per_month=50000, sso_enabled=off
   POST /items/enterprise-plan/item_entitlements
     ... seats=unlimited, api_calls_per_month=1000000, sso_enabled=on
   ```
3. Product code:
   ```python
   if not can_do(customer_id, "sso_enabled"):
       redirect_to_upgrade()
   if seats_in_use(customer_id) >= entitlement(customer_id, "seats"):
       raise QuotaExceeded("Add a seat or upgrade your plan.")
   ```
4. Sales-led override for a strategic Enterprise prospect:
   ```bash
   POST /subscriptions/{id}/subscription_entitlements
     entitlements[feature_id][0]=api_calls_per_month
     entitlements[value][0]=5000000
   ```
   The override carries through `subscription_entitlements` retrieval until revoked.
