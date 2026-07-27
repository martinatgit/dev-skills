---
name: chargebee
description: Chargebee billing and subscription development guidance for senior engineers. Use this skill whenever the user is working with Chargebee in any way - subscriptions, invoices, customers, item_prices, hosted checkout, Chargebee.js, payment intents (3DS/SCA), webhooks/events, dunning, taxes, entitlements/features, Product Catalog 1.0 or 2.0, MCP servers, or any official Chargebee SDK (Node, Python, PHP, Java, Go, Ruby, .NET, Laravel, Next.js). Triggers on the literal token "chargebee" (case-insensitive), URLs under chargebee.com or apidocs.chargebee.com, the base URL pattern "*.chargebee.com/api/v2", the header "chargebee-idempotency-key", event names like "subscription_created", "subscription_renewed", "payment_succeeded", "payment_failed", "customer_changed", and on tasks framed as "integrate billing", "set up subscription billing", "implement checkout", "handle 3DS or SCA", "process Chargebee webhooks", "fix failed payment retries / dunning", "build entitlements gate / feature flag from plan", "migrate Product Catalog 1.0 to 2.0", "configure metered/usage billing", "write a Chargebee tutorial / explainer / worked example", or "debug a Chargebee error". Provides concept identification, recommended implementation patterns, debugging playbooks, and worked examples. Loads detailed references on demand.
---

# Chargebee Development Skill

This skill primes the agent for any Chargebee-related task: implementation, integration, debugging, tutorial authoring, and worked examples. It is hierarchical: this file is the entry point; deep knowledge lives in `references/` and is loaded only when relevant.

## Step 0: Identify the task type

Before touching code, classify the user request into one of these categories and load the corresponding reference. Do not load files you do not need.

| Task signal | Load |
|---|---|
| First-time setup, "how do I start", architecture decisions | `references/implementation_guide.md` |
| Auth, base URL, pagination, errors, idempotency, rate limits, env model | `references/api.md` |
| Plans, addons, charges, item_prices, families, pricing models, PC 1.0 vs 2.0 | `references/product_catalog.md` |
| Create, change, pause, resume, cancel, reactivate a subscription | `references/subscriptions.md` |
| Customer object, payment_sources, payment_intents, 3DS/SCA, gateways | `references/customers_payment.md` |
| Invoices, credit notes, refunds, proration, taxes, dunning, write-off | `references/invoices_billing.md` |
| Event types, webhook delivery, retries, ordering, signing, replay | `references/webhooks_events.md` |
| Hosted Checkout, Hosted Portal, Chargebee.js Drop-In, custom UI, mobile SDKs | `references/hosted_chargebeejs.md` |
| Feature gating, plan-to-feature mapping, quota enforcement | `references/entitlements.md` |
| Error triage, "why is X failing", reproduction steps | `references/debugging.md` |
| Tutorial, explainer, worked example, demo project | `references/examples.md` |
| Concept lookup, glossary, mental model, mindmap | `references/concepts.md` and `references/mindmap.md` |
| Sources, deep-dive URLs | `references/sources.md` |

If two or more categories apply, load `references/concepts.md` first to orient, then the specific files.

## Step 1: Confirm constraints before writing code

Ask the user (or check the repo) for these before generating non-trivial code. Do not assume defaults silently.

1. **Site environment**: test site or live site? (URL pattern `{site}.chargebee.com`, API keys differ.)
2. **Product Catalog version**: 1.0 (plans/addons) or 2.0 (items/item_prices). Endpoints and field names differ. See `references/product_catalog.md`.
3. **SDK / language**: Node, Python, PHP, Java, Go, Ruby, .NET, Laravel, Next.js, or raw HTTP. Use the official SDK unless there is a documented reason not to.
4. **API version pinning**: client library version must match the `api_version` on events the consumer will see.
5. **Payment gateway**: Stripe, Adyen, Braintree, etc. Some flows (3DS, dunning behaviour, supported methods) are gateway-specific.
6. **Region / data residency**: site domain encodes data centre (US, EU, AU). MCP server endpoints follow `{site}.mcp.chargebee.com`.

State the assumed values explicitly in the response if they cannot be confirmed.

## Step 2: Apply the always-true rules

These hold for every Chargebee integration. Violations are the most common bug sources.

1. **Idempotency on every POST**. Generate a UUID per logical action and send it as `chargebee-idempotency-key`. Replay returns the original response with `chargebee-idempotency-replayed: true`. Estimate APIs do not support idempotency; do not send the header there. See `references/api.md`.
2. **Webhooks may arrive out of order and duplicated**. Persist `event.id` for de-duplication (window: ~3 days 7 hours). Compare `content.<resource>.resource_version` (millisecond timestamp) before applying; ignore lower values. See `references/webhooks_events.md`.
3. **Webhooks are asynchronous**. For time-critical reads, use the List Events / Retrieve Event API after acting, not webhooks alone.
4. **Webhook handler must return 2XX fast**. Chargebee allows up to **20 s total** on test sites and **60 s total** on live sites before treating the call as failed. Failed deliveries are retried up to **7 times** (at +2 m, +6 m, +30 m, +1 h, +5 h, +1 d, +2 d). Do heavy work async; ack first. Also note the **5-endpoint-per-site cap** when planning consumers.
5. **Test on the test site only**. Time Machine, the Chargebee Test Gateway, and Auto-Populate are test-site features. Use Transfer Configurations to promote settings.
6. **Form-encoded requests, JSON responses**. Single resources wrap in `{ "<resource>": { ... } }`. Lists return `{ "list": [ ... ] }` with `next_offset`.
7. **Currency is in minor units (cents)**. `amount` fields are integers.
8. **Timestamps are Unix epoch seconds**.
9. **Decouple billing from feature gating**. Use Entitlements/Features. Do not hard-code plan ids in product code. See `references/entitlements.md`.
10. **PCI scope**: never send raw card data through your backend. Tokenize via Chargebee.js (Drop-In or Components). See `references/hosted_chargebeejs.md`.

## Step 3: Match the implementation pattern

For implementation work, pick the lowest-PCI-scope pattern that satisfies the requirements. In order of increasing engineering cost:

1. **Hosted Checkout + Hosted Portal**: zero front-end work, Chargebee-hosted UI. Use for MVPs, internal tools, or low-customisation merchants.
2. **Chargebee.js Drop-In**: embedded checkout on your domain, customised styling, no PCI scope on the card field. Default recommendation.
3. **Chargebee.js Components**: build your own UI with tokenised card fields (`cbCard`, `cbNumber`, etc.). Use when Drop-In is too rigid.
4. **Direct API with Payment Intents**: full custom UI, you orchestrate 3DS via Chargebee.js helpers. Use only when 1-3 are unworkable.

See `references/hosted_chargebeejs.md` for the decision matrix and code snippets.

## Step 4: Debug methodically

For any Chargebee error, follow the triage flow in `references/debugging.md`. Do not guess. The canonical inputs are:

- The full HTTP request (method, URL, headers including `chargebee-idempotency-key`, body).
- The full HTTP response (`http_status_code`, `api_error_code`, `error_code`, `message`, `param`).
- For webhook bugs: the `event.id`, `event_type`, `api_version`, `source`, and the receiver's processing log.
- For payment bugs: the gateway-side reference (Stripe `pi_*`, Adyen `pspReference`, etc.).

## Step 5: Reference the canonical documentation

Always cite the official URL when explaining a concept to the user. Authoritative roots:

- API reference: `https://apidocs.chargebee.com/docs/api/`
- Product docs: `https://www.chargebee.com/docs/`
- API Explorer (live request builder): `https://api-explorer.chargebee.com/`
- OpenAPI spec: `https://github.com/chargebee/openapi`
- Changelog: `https://www.chargebee.com/help/api-updates/`

A complete URL index by topic is in `references/sources.md`.

## Authoring tutorials, explainers, and worked examples

When the request is teaching rather than building:

1. Start by loading `references/concepts.md` for the canonical vocabulary and `references/mindmap.md` for the structure of the explanation.
2. Pick a single concrete user story and walk it end-to-end (signup -> first invoice -> renewal -> webhook -> portal update).
3. Use the worked examples in `references/examples.md` as scaffolds. They cover: SaaS subscription with 3DS, usage-based billing, hosted checkout, webhook handler, and entitlements gate.
4. State the Chargebee version assumption (Product Catalog 2.0 unless otherwise specified) and the SDK used.

## Hard limits

- Do not write Chargebee API keys, gateway secrets, or webhook auth credentials into files, code samples, or commit messages. Use environment variables (`CHARGEBEE_SITE`, `CHARGEBEE_API_KEY`) and call them out explicitly.
- Do not implement payment flows that bypass Chargebee.js tokenisation. Raw PAN must never reach the merchant backend.
- Do not call live-site endpoints for testing. Always confirm `CHARGEBEE_SITE` resolves to a test site during development.
