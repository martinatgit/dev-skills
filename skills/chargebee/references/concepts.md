# Chargebee Core Concepts

Canonical vocabulary and mental model. Load this when the user asks "what is X", "how does X relate to Y", or when you need the right term before writing code.

## Table of contents

1. Account topology (site, business entities)
2. Identity and access (API keys, users)
3. Product Catalog (items, item_prices, families)
4. Customer and contact model
5. Subscription lifecycle
6. Billing artefacts (invoices, credit notes, transactions, payments)
7. Payment plumbing (gateway accounts, payment sources, payment intents)
8. Customer-facing UI (hosted pages, Chargebee.js, portal)
9. Eventing (events, webhooks)
10. Entitlements (features)
11. Revenue operations (dunning, taxes, proration, revenue recognition)
12. Testing surface (test site, Time Machine, sandbox)
13. AI/MCP surface

## 1. Account topology

- **Site**: a tenant inside Chargebee, addressed as `{site}.chargebee.com`. Every account has a test site and (after go-live) a live site. The site URL encodes the data centre (US, EU, AU).
- **Business Entity**: a sub-tenant inside a site used to model multiple legal entities (e.g. US LLC and EU GmbH) with isolated catalogue, invoicing, tax, and accounting. Customers, subscriptions, and invoices belong to one entity. A customer can be moved between entities via the Move operation.

## 2. Identity and access

- **API key**: server-side credential, used via HTTP Basic Auth with the key as username and empty password. Types: Full-Access, Read-Only, App-specific. Test-site and live-site keys are separate. Never embed in client code.
- **Publishable key**: client-side, used by Chargebee.js for tokenisation. Safe to expose.
- **User**: human admin with role-based access in the Chargebee UI. Distinct from API key identity.

## 3. Product Catalog

There are two versions of the catalogue. They cannot be mixed within a site.

**Product Catalog 2.0 (current)**:
- **Item Family**: organisational container grouping related items.
- **Item**: the saleable concept. `type` is `plan`, `addon`, or `charge`. Has `id`, `name`, `status` (`active`, `archived`, `deleted`), `is_shippable`, `enabled_in_portal`, `metered`, `usage_calculation` (`sum_of_usages`, `last_usage`, `max_usage`).
- **Item Price**: a specific price point for an item (currency, period, period_unit, price model). One item can have many item_prices (e.g. monthly, yearly, USD, EUR).
- **Attached Item**: a recurring item bundled with another item by default at subscription creation.
- **Differential Price**: an item_price that overrides the base price for a specific plan combination.

**Product Catalog 1.0 (legacy)**:
- **Plan**, **Addon**, **Charge** as top-level objects. No item layer. New integrations should not use 1.0.

**Price models** (apply to item_prices):
- `flat_fee`: fixed price per cycle.
- `per_unit`: price multiplied by quantity.
- `tiered`: each unit charged at its tier's rate, summed.
- `volume`: all units charged at the tier rate matching total quantity.
- `stairstep`: package-style pricing where price is a step function of quantity.
- `unlimited`: no quantity multiplier.

## 4. Customer and contact model

- **Customer**: subscriber, individual or organisation. Fields include `id`, `email`, `billing_address`, `payment_method`, `auto_collection` (`on`/`off`), `net_term_days`, `taxability`, `vat_number`. Auto-generated id if not supplied.
- **Contact**: additional email recipients on a customer (e.g. billing@, accounts@).
- **Customer-Subscription cap**: max 900 subscriptions per customer (active or inactive combined).

## 5. Subscription lifecycle

Subscription is the link between a customer and one or more item_prices.

**Statuses**:
- `future`: scheduled to start later.
- `in_trial`: trial period running.
- `active`: billing on cycle.
- `non_renewing`: will end at term end, no further renewal.
- `paused`: suspended, will not renew while paused.
- `cancelled`: terminated.
- `transferred`: moved to another business entity.

**Common transitions**:
- create -> in_trial / active / future
- in_trial -> active (trial_end reached)
- active -> non_renewing (cancel scheduled at term end)
- active -> cancelled (cancel immediately)
- active -> paused (pause)
- paused -> active (resume)
- cancelled -> active (reactivate, within retention window)

## 6. Billing artefacts

- **Invoice**: bill issued for a subscription term, charge, or one-off. Statuses: `paid`, `posted`, `payment_due`, `not_paid`, `voided`, `pending`.
- **Credit Note**: negative invoice issued for refund, adjustment, or write-off. Adjustment credit notes are linked back to the source invoice.
- **Transaction**: a money movement attempt (authorisation, capture, refund). Has its own status; multiple transactions can attach to one invoice.
- **Pending Invoice**: not yet closed (e.g. mid-cycle metered billing). Closes at term end or on demand.

## 7. Payment plumbing

- **Gateway Account**: connection to a payment processor (Stripe, Adyen, Braintree, etc.). Multiple gateways per site supported; routing by currency or business entity.
- **Payment Source**: a tokenised payment instrument attached to a customer (card, bank account, PayPal, etc.). Replaces the older `payment_method` concept for multi-method customers.
- **Payment Intent**: a Chargebee-managed intent used for 3DS/SCA flows. Statuses: `inited`, `in_progress`, `authorized`, `consumed`, `expired`. Expires in 1 hour if unconsumed. Passed from front-end (Chargebee.js) to back-end and supplied to subscription/charge creation.

## 8. Customer-facing UI

- **Hosted Page**: a Chargebee-hosted URL for a specific flow. Types: `checkout_new`, `checkout_existing`, `manage_payment_sources`, `collect_now`, `update_payment_method`, `update_card`, `extend_subscription`, `accept_quote`, `checkout_one_time`, `pre_cancel`, `view_voucher`. State machine: `created -> requested -> succeeded/cancelled -> acknowledged`. Checkout URLs expire in 3 hours; collect_now and manage_payment_sources URLs expire in 5 days.
- **Hosted Portal (Customer Portal)**: long-running self-service area where the customer can view invoices, manage subscriptions, update payment methods, and download statements. Authenticated via portal session.
- **Chargebee.js**: client-side library for tokenisation, embedded checkout (Drop-In), and reusable Components. Required for 3DS handling.
- **Mobile SDK**: native iOS/Android SDKs wrapping checkout and portal flows.

## 9. Eventing

- **Event**: record of a state change on the site. Fields: `id`, `occurred_at`, `source` (`admin_console`, `api`, `scheduled_job`, `hosted_page`, `portal`, `external_service`, `js_api`, `bulk_operation`, `webhook`), `user`, `event_type`, `api_version`, `content` (resource snapshots), `webhooks` (delivery statuses).
- **Webhook**: HTTP POST callback delivering an event payload to a configured URL. Authentication via Basic Auth or random key in URL. Retries up to 7 times over ~2 days on failure (at +2 m, +6 m, +30 m, +1 h, +5 h, +1 d, +2 d). Total handler budget: 20 s on test, 60 s on live. Up to 5 endpoints per site.
- **Resource version**: `resource_version` on event content is a millisecond timestamp used to reorder events. Apply only if newer than the last seen value for that resource id.

## 10. Entitlements

- **Feature**: a unit of product capability (e.g. "API calls", "Seats", "SSO enabled"). Created independently of plans.
- **Entitlement**: the mapping between a plan-item (or addon-item) and a feature value. The product code consults entitlements, not plan ids, to decide whether the customer can use a capability. This decouples pricing changes from product code changes.

## 11. Revenue operations

- **Dunning**: retry policy for failed payments. Two modes: Smart Dunning (up to 12 retries, auto-tuned) and Custom Dunning (up to 5 retries on a configured day-offset list). Terminal action is configurable: cancel subscription, mark `not_paid`, void, write-off, or reverse (creates Credit Note).
- **Tax**: configurable per region. Avalara, TaxJar, EU VAT, Manual, or Chargebee Tax. Prices can be tax-inclusive or tax-exclusive.
- **Proration**: for mid-cycle plan changes, billing modes include `prorated`, `not_prorated`, `bill_immediately`, `defer_billing`.
- **Calendar Billing**: aligns billing dates to month boundaries (e.g. always bill on the 1st).
- **Net Terms**: invoice due_date offset by `net_term_days` from issue date (NET 30 etc.).
- **Consolidated Invoicing**: groups multiple subscriptions for one customer into a single invoice per cycle.
- **Revenue Recognition**: ASC 606 / IFRS 15 support including deferred revenue schedules and journal entries.

## 12. Testing surface

- **Test Site**: full Chargebee instance with no real money movement. Includes the Chargebee Test Gateway.
- **Time Machine**: simulate the passage of time on the test site to trigger renewals, dunning, scheduled changes, and webhooks. Not available on live sites.
- **Auto-Populate**: bootstrap a test site's catalogue from a pricing page URL.
- **Transfer Configurations**: copy settings (plans, emails, branding, webhooks) from test to live.
- **Go-Live Checklist**: gating step before the live site accepts traffic.

## 13. AI/MCP surface

Chargebee provides three official Model Context Protocol servers:
- **Knowledge Base MCP**: answers documentation and API questions, generates code snippets.
- **Data Access MCP**: queries the site for customers, subscriptions, invoices, transactions, quotes, events.
- **Onboarding MCP**: assists with product catalogue setup on test sites.

Endpoint pattern: `https://{site}.mcp.chargebee.com/{agent}` where `{agent}` is `knowledge_base_agent`, `data_lookup_agent`, or `onboarding_agent`. Auth supports API key or OAuth (OAuth restricts tools to the connected user's permissions).
