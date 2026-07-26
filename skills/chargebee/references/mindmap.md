# Chargebee Mindmap

A hierarchical mental model of Chargebee. Use to orient new contributors, to identify which concept a user is actually asking about, or to structure an explainer.

The mindmap is also expressed in `concepts.md` as text. This file presents the same structure in indented form for quick scanning, with cross-references.

## Top-level decomposition

```
Chargebee
├── Account topology                                  [concepts.md §1]
│   ├── Site
│   │   ├── Test site
│   │   │   ├── Chargebee Test Gateway
│   │   │   ├── Time Machine
│   │   │   └── Auto-Populate
│   │   └── Live site
│   │       └── Go-Live Checklist
│   └── Business Entity
│       ├── Catalogue isolation
│       ├── Invoicing isolation
│       ├── Tax / accounting isolation
│       └── Move (customer between entities)
│
├── Identity & access                                 [concepts.md §2, api.md]
│   ├── API key
│   │   ├── Full-Access
│   │   ├── Read-Only
│   │   └── App-specific
│   ├── Publishable key (Chargebee.js)
│   └── User (admin)
│
├── Product Catalog                                   [product_catalog.md]
│   ├── PC 2.0 (current)
│   │   ├── Item Family
│   │   ├── Item
│   │   │   ├── plan
│   │   │   ├── addon
│   │   │   └── charge
│   │   ├── Item Price
│   │   │   └── Price model
│   │   │       ├── flat_fee
│   │   │       ├── per_unit
│   │   │       ├── tiered
│   │   │       ├── volume
│   │   │       ├── stairstep
│   │   │       └── unlimited
│   │   ├── Attached Item
│   │   ├── Differential Pricing
│   │   └── Metered / Usage
│   │       └── usage_calculation: sum_of_usages | last_usage | max_usage
│   ├── PC 1.0 (legacy)
│   │   ├── Plan
│   │   ├── Addon
│   │   └── Charge
│   └── Coupons
│
├── Customer & contact model                          [customers_payment.md]
│   ├── Customer
│   │   ├── auto_collection (on/off)
│   │   ├── net_term_days
│   │   ├── taxability
│   │   ├── vat_number
│   │   └── billing_address
│   └── Contact (additional recipients)
│
├── Subscription                                      [subscriptions.md]
│   ├── State machine
│   │   ├── future
│   │   ├── in_trial
│   │   ├── active
│   │   ├── non_renewing
│   │   ├── paused
│   │   ├── cancelled
│   │   └── transferred (cross-entity)
│   ├── Lifecycle ops
│   │   ├── create_with_items
│   │   ├── update_for_items
│   │   ├── pause / resume
│   │   ├── cancel / reactivate
│   │   ├── change at term end (scheduled changes)
│   │   └── remove_scheduled_changes
│   └── Composition
│       ├── plan-item-price (exactly one)
│       ├── addon-item-prices (zero or more)
│       ├── charge-item-prices (one-off)
│       └── coupon_ids
│
├── Billing artefacts                                 [invoices_billing.md]
│   ├── Invoice
│   │   ├── status: paid | posted | payment_due | not_paid | voided | pending
│   │   └── ops: create, charge, collect_payment, refund, void, write_off, apply_credits
│   ├── Credit Note
│   │   ├── adjustment
│   │   └── refundable
│   ├── Transaction
│   │   └── status: success | failure | voided | timeout | needs_attention
│   └── Pending Invoice
│
├── Payment plumbing                                  [customers_payment.md]
│   ├── Gateway Account
│   ├── Payment Source
│   │   └── types: card, bank_account, direct_debit, paypal, apple_pay, google_pay, ...
│   └── Payment Intent (3DS / SCA)
│       └── status: inited | in_progress | authorized | consumed | expired
│
├── Customer-facing UI                                [hosted_chargebeejs.md]
│   ├── Hosted Pages
│   │   └── types: checkout_new, checkout_existing, manage_payment_sources,
│   │              collect_now, extend_subscription, accept_quote,
│   │              checkout_one_time, pre_cancel, view_voucher
│   ├── Chargebee.js
│   │   ├── Drop-In
│   │   └── Components (cbCard, cbNumber, ...)
│   ├── Hosted Portal (Customer Portal)
│   └── Mobile SDKs (iOS, Android)
│
├── Eventing                                          [webhooks_events.md]
│   ├── Event
│   │   ├── id, occurred_at, source, user, event_type, api_version, content
│   │   └── resource_version (ordering key)
│   ├── Webhook
│   │   ├── POST application/json
│   │   ├── Basic Auth + IP allowlist
│   │   ├── Retries up to 2 days
│   │   └── Out-of-order delivery
│   └── Polling (Events API)
│
├── Entitlements                                      [entitlements.md]
│   ├── Feature
│   │   └── type: switch | quantity | range | custom
│   └── Item Entitlement / Subscription Entitlement
│
├── Revenue operations                                [invoices_billing.md]
│   ├── Dunning (Smart | Custom)
│   ├── Taxes (Chargebee Tax, Avalara, TaxJar, Manual)
│   ├── Proration (prorate, end_of_term, invoice_immediately)
│   ├── Net Terms
│   ├── Consolidated Invoicing
│   └── Revenue Recognition (ASC 606 / IFRS 15)
│
├── Testing surface                                   [concepts.md §12]
│   ├── Test Site
│   ├── Time Machine
│   ├── Auto-Populate
│   └── Transfer Configurations
│
└── AI / MCP surface                                  [concepts.md §13]
    ├── Knowledge Base MCP
    ├── Data Access MCP
    └── Onboarding MCP
```

## Cross-cutting axes

Some concerns cut across the tree. Track them separately when designing:

1. **Idempotency**: applies to every server-side mutation and every webhook receive.
2. **Resource versioning**: applies to every event consumer.
3. **Environment isolation**: applies to every endpoint, every key, every webhook URL, every MCP URL.
4. **PCI scope**: determined by where card data appears; aim for SAQ-A via tokenisation.
5. **Multi-currency / multi-entity**: pervasive once introduced; design upfront.

## Use this mindmap to identify the right concept

When a user asks something fuzzy, walk down the tree:

- "How do I let users change their card?" -> Customer-facing UI -> Hosted Portal **or** Hosted Page `manage_payment_sources`.
- "Why did the same webhook arrive twice?" -> Eventing -> Webhook retries -> de-dup on `event.id`.
- "How do I price by usage?" -> Product Catalog -> Item with `metered=true` -> Item Price with `per_unit` or `tiered` -> Subscription with Usages API.
- "How do I gate the SSO feature behind Enterprise?" -> Entitlements -> Feature type `switch` -> Item entitlement on plan.
- "How do I retry a failed card 3 days later?" -> Revenue ops -> Dunning -> Custom Dunning with day-offset list.
