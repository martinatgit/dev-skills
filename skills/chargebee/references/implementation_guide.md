# Implementation Guide

Sequential setup playbook from new site to live traffic. Load when scoping a new Chargebee integration, sequencing work, or auditing a half-done one.

Derived from: <https://www.chargebee.com/docs/billing/2.0/implementing-chargebee/implementation_guide>

## Phases

### Phase 1: Basic settings

1. Sign up: <https://www.chargebee.com/trial-signup/>. Two sites are provisioned (test + live).
2. Invite team members per site. Roles: admin, billing, support, read-only, custom. Test and live require separate invitations.
3. Configure currencies and frequencies. Decide multi-currency strategy now; retrofitting affects historic data.
4. Set time zone. Affects renewal timing.
5. Set default tax engine if known. See `references/invoices_billing.md` section 5.

Reference: <https://www.chargebee.com/docs/billing/2.0/getting-started/sites-intro>

### Phase 2: Product Catalog setup

1. Choose version. New sites default to PC 2.0. Stay on 2.0 unless there is an explicit reason.
2. Create item families. One family per product line.
3. Create items (`plan`, `addon`, `charge`). Decide `metered` early; switching later disrupts billing.
4. Create item prices: one per currency, period, and pricing tier. Use stable id conventions (`<item>-<period>-<currency>`).
5. Configure attached items for default bundles.
6. Configure differential pricing for plan-addon combinations.
7. Configure coupons.

See `references/product_catalog.md`.

### Phase 3: Payment gateway configuration

1. Add a gateway account. Reference: <https://www.chargebee.com/docs/payments/2.0/payment-gateways-and-configuration/gateway_settings>.
2. Connect the test gateway for development. Chargebee Test Gateway is always available.
3. Enable payment methods (card, direct debit, wallets, BNPL).
4. Configure 3DS / SCA settings per gateway.
5. For multi-currency or multi-entity, route gateways by currency or business entity.

### Phase 4: Customer signup process

Choose one pattern, document the choice:

- **Self-serve via Hosted Checkout** (lowest effort).
- **Self-serve via Drop-In on your domain** (default for SaaS).
- **Self-serve via Components** (custom UI).
- **Sales-led via Quote acceptance** (B2B, contracts).
- **Backend import / migration** for existing customers.

See `references/hosted_chargebeejs.md`.

### Phase 5: Webhook integration

1. Create a webhook endpoint configuration in admin per environment.
2. Set Basic Auth credentials (random key recommended).
3. Allowlist Chargebee outbound IPs on your edge.
4. Build the consumer following the pattern in `references/webhooks_events.md` section 7.
5. Subscribe to the minimal event set first (`subscription_*`, `invoice_*`, `payment_*`); expand as needed.
6. Test with the "Test webhook" button and Time Machine.

### Phase 6: Billing configuration

1. Decide proration behaviour for mid-term changes: on or off by default.
2. Decide billing alignment: calendar billing (everyone bills on the 1st) vs anniversary billing.
3. Configure net terms if B2B / invoice-pay (`net_term_days`).
4. Configure consolidated invoicing if multiple subscriptions per customer is common.
5. Configure pending invoices for metered items.
6. Configure dunning: pick Smart or Custom; set terminal action.

See `references/invoices_billing.md`.

### Phase 7: Customer-facing essentials

1. Branding: logo, colours, fonts.
2. Localisation: supported languages and per-customer language.
3. Email Notifications v2: enable templates, customise copy, configure sender.
4. Customer Portal: enable, configure permissions.
5. Entitlements: define features, attach to items. See `references/entitlements.md`.

### Phase 8: Testing and launch

1. End-to-end smoke tests on the test site:
   - Signup -> first invoice -> payment success.
   - Signup -> first invoice -> payment failure -> dunning retries -> recovery.
   - Mid-term plan change with proration.
   - Cancel at term end, then reactivate.
   - Trial -> active conversion.
   - Webhook receiver receives expected event types in order, idempotently.
2. Time Machine simulations: advance time to verify renewal, trial end, dunning, and reminders fire.
3. Transfer Configurations to live site: Settings > Configure Chargebee > Transfer Configurations.
4. Swap to live API keys in the application.
5. Complete the Go-Live Checklist: <https://www.chargebee.com/docs/billing/2.0/implementing-chargebee/checklist>.
6. Switch DNS / launch.
7. Watch the first 72 hours: webhook delivery rates, dunning hit rate, gateway decline rate.

## Pre-launch checklist (condensed)

- [ ] Test site smoke tests green.
- [ ] Time Machine scenarios green.
- [ ] Configurations transferred to live.
- [ ] Live API keys provisioned and stored in secrets manager. No keys in code.
- [ ] Webhook endpoints configured on live site with Basic Auth and IP allowlist.
- [ ] Webhook consumer deployed and acking 2XX < 5s on staging.
- [ ] Idempotency keys generated on every server-side mutation.
- [ ] Dunning + email notifications configured.
- [ ] Tax engine connected and tested with non-zero rates.
- [ ] Backups: scheduled exports configured.
- [ ] Monitoring: alert on `payment_failed` spike, on webhook 5xx, on API 5xx.
- [ ] Runbook for first-week incidents documented.

## Decision points worth flagging early

- **PC 1.0 vs 2.0**: 2.0 by default. Cannot switch a live site without Chargebee Support.
- **Single site vs multiple sites**: separate sites for QA, staging, production add ops burden but isolate risk.
- **Single business entity vs multi-entity**: only relevant for multiple legal entities or revenue recognition splits.
- **Calendar vs anniversary billing**: calendar simplifies finance close, anniversary maximises revenue smoothing.
- **Auto-collection on vs off per segment**: SaaS = on; enterprise = often off with NET-D.
- **Smart vs Custom dunning**: Smart if available on plan; Custom if you need deterministic timing for compliance.
