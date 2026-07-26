# Worked Examples

End-to-end patterns the agent can adapt. Load when authoring tutorials, scaffolding new integrations, or answering "show me how to do X".

All examples use Product Catalog 2.0, Python SDK, idiomatic Node/JS where front-end is involved. Translate to other SDKs as needed; the HTTP semantics are identical.

## Table of contents

1. Minimal SaaS signup with 3DS via Drop-In
2. Server-side subscription creation with existing token
3. Usage-based billing with metered items
4. Hosted checkout with redirect and acknowledge
5. Webhook handler (Flask) with de-dup and ordering
6. Entitlements check in a request middleware
7. Trial-to-paid conversion with reminder
8. One-time credit purchase: hosted checkout + grant via webhook
9. Refund flow

## 1. Minimal SaaS signup with 3DS via Drop-In

Goal: a logged-out visitor lands on the pricing page, picks Pro, completes 3DS in a Chargebee.js Drop-In, lands back on a "welcome" page with an active subscription.

Front-end:
```html
<script src="https://js.chargebee.com/v2/chargebee.js"
        data-cb-site="acme-test"></script>
<a href="#"
   data-cb-type="checkout"
   data-cb-item-0="pro-monthly-usd"
   data-cb-item-0-quantity="1"
   data-cb-customer-email="">Subscribe to Pro</a>
<script>
  const cb = Chargebee.getInstance();
  cb.setCheckoutCallbacks(() => ({
    success: async (hostedPageId) => {
      const r = await fetch("/checkout/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hosted_page_id: hostedPageId }),
      });
      const { subscription_id } = await r.json();
      location.href = "/welcome?sub=" + subscription_id;
    },
  }));
</script>
```

Backend:
```python
from chargebee import Chargebee
chargebee.configure({"api_key": os.environ["CHARGEBEE_API_KEY"], "site": os.environ["CHARGEBEE_SITE"]})

@app.post("/checkout/complete")
def complete():
    hp_id = request.json["hosted_page_id"]
    hp = chargebee.HostedPage.retrieve(hp_id).hosted_page
    if hp.state != "succeeded":
        return {"error": "checkout_incomplete"}, 400
    chargebee.HostedPage.acknowledge(hp_id)
    sub_id = hp.content["subscription"]["id"]
    return {"subscription_id": sub_id}
```

Why this works:
- The Drop-In iframe handles tokenisation and 3DS; no card data on your domain.
- `acknowledge` closes the hosted page lifecycle (idempotent).
- The `success` callback gives the `hosted_page_id`; do not trust the customer's browser to assert the subscription was created. Verify server-side.

## 2. Server-side subscription creation with existing token

Goal: backend already holds a card token (e.g. from a Chargebee.js Components form) and creates a subscription with idempotency.

```python
import uuid

def create_subscription(customer_id: str, item_price_id: str, token: str) -> str:
    idem_key = str(uuid.uuid4())

    payment_source = chargebee.PaymentSource.create_using_token({
        "customer_id": customer_id,
        "token": token,
    }, headers={"chargebee-idempotency-key": idem_key + ":ps"}).payment_source

    result = chargebee.Subscription.create_with_items(customer_id, {
        "subscription_items": [{
            "item_price_id": item_price_id,
            "quantity": 1,
        }],
        "payment_source_id": payment_source.id,
    }, headers={"chargebee-idempotency-key": idem_key + ":sub"})

    return result.subscription.id
```

Note: idempotency keys differ per logical op; do not reuse the same key for two different operations.

## 3. Usage-based billing with metered items

Setup:
- Item: `api_calls`, `type=charge`, `metered=true`, `usage_calculation=sum_of_usages`.
- Item price: `api-calls-per-1k`, `pricing_model=per_unit`, `price=100` (cents per 1k).

Subscribe a customer to plan + metered addon:
```python
chargebee.Subscription.create_with_items("cust_123", {
    "subscription_items": [
        {"item_price_id": "pro-monthly-usd"},
        {"item_price_id": "api-calls-per-1k"},
    ],
})
```

Record usage as it happens:
```python
def record_api_call_usage(sub_id: str, calls: int):
    chargebee.Usage.create(sub_id, {
        "item_price_id": "api-calls-per-1k",
        "quantity": str(calls // 1000),
        "usage_date": int(time.time()),
        "dedupe_option": "ignore",   # silently skip duplicate timestamps
    })
```

At cycle close, Chargebee bills `sum_of_usages` times the per-unit price.

## 4. Hosted checkout with redirect and acknowledge

Server endpoint that issues the URL and the return handler:
```python
@app.post("/start-checkout")
def start_checkout():
    body = request.json
    hp = chargebee.HostedPage.checkout_new_for_items({
        "subscription_items": [{"item_price_id": body["item_price_id"], "quantity": 1}],
        "customer": {"email": body["email"]},
        "redirect_url": "https://app.example.com/checkout/return",
        "pass_thru_content": json.dumps({"order_id": body["order_id"]}),
    }).hosted_page
    return {"url": hp.url}

@app.get("/checkout/return")
def checkout_return():
    hp_id = request.args["id"]
    hp = chargebee.HostedPage.retrieve(hp_id).hosted_page
    if hp.state == "succeeded":
        chargebee.HostedPage.acknowledge(hp_id)
        meta = json.loads(hp.pass_thru_content or "{}")
        return render("checkout_ok.html", order_id=meta.get("order_id"))
    return render("checkout_cancelled.html"), 400
```

## 5. Webhook handler (Flask) with de-dup and ordering

```python
@app.post("/webhooks/chargebee")
def chargebee_webhook():
    # 1. AuthN: Basic Auth and Chargebee IP allowlist enforced at the load balancer.
    event = request.get_json(force=True)
    event_id = event["id"]
    event_type = event["event_type"]
    api_ver = event["api_version"]

    if api_ver != "v2":
        log.warning("api_version skew", got=api_ver)
        return "", 200

    with db.transaction():
        # de-dup
        if db.execute(
            "INSERT INTO processed_events(event_id, received_at) VALUES (%s, NOW()) "
            "ON CONFLICT (event_id) DO NOTHING RETURNING event_id",
            (event_id,)
        ).rowcount == 0:
            return "", 200

    queue.enqueue(handle_event_async, event_id, event_type, event["content"])
    return "", 200


def handle_event_async(event_id: str, event_type: str, content: dict):
    if event_type.startswith("subscription_"):
        sub = content["subscription"]
        rv = int(sub["resource_version"])
        with db.transaction():
            row = db.fetchone("SELECT resource_version FROM subscriptions WHERE id=%s", (sub["id"],))
            if row and rv <= row["resource_version"]:
                return  # stale, drop
            db.upsert("subscriptions", id=sub["id"], status=sub["status"],
                      current_term_end=sub["current_term_end"], resource_version=rv,
                      raw=json.dumps(sub))
    elif event_type == "payment_failed":
        notify_revops(content["transaction"], content["invoice"])
    # ... other branches
```

## 6. Entitlements check in a request middleware

```python
class EntitlementsMiddleware:
    def __init__(self, app): self.app = app

    def __call__(self, environ, start_response):
        cust_id = environ.get("HTTP_X_CUSTOMER_ID")
        if cust_id:
            environ["entitlements"] = self.load(cust_id)
        return self.app(environ, start_response)

    @lru_cache(maxsize=10_000)
    def load(self, cust_id):
        sub = current_subscription(cust_id)
        if not sub:
            return {}
        entries = chargebee.SubscriptionEntitlement.list(sub.id).entitlements
        return {e.feature_id: e.value for e in entries}
```

Invalidate on `subscription_*` webhook by purging the cache entry for the customer.

## 7. Trial-to-paid conversion with reminder

Setup:
- Item price `pro-monthly-usd` with `trial_period=14`, `trial_period_unit=day`.
- Webhook subscriber on `subscription_trial_end_reminder` (sent ~3 days before trial end).

Backend:
```python
def on_trial_end_reminder(event):
    sub = event["content"]["subscription"]
    cust = event["content"]["customer"]
    if not has_payment_source(cust["id"]):
        send_email(cust["email"], "Add a card to keep your account",
                   portal_url=create_portal_session(cust["id"]).access_url)

def on_subscription_activated(event):
    sub = event["content"]["subscription"]
    grant_full_access(sub["customer_id"], sub["id"])
```

The transition `in_trial -> active` is automatic at `trial_end` if a payment source is on file; otherwise Chargebee retries via dunning configuration.

## 8. One-time credit purchase: hosted checkout + grant via webhook

Goal: the customer buys a "100 credits" pack as a one-time purchase. The webhook receiver grants credit only after money has actually moved.

Setup (Product Catalog 2.0):
- Item: `credit-pack`, `type=charge`.
- Item Prices: `credit-100-usd` (price 1000 cents = USD 10.00), `credit-500-usd`, etc.
- Webhook: subscribe to `payment_succeeded`, `payment_refunded`, `credit_note_created`, `invoice_voided`.

Front-end - launch a one-time hosted checkout:
```python
hp = chargebee.HostedPage.checkout_one_time_for_items_charges({
    "customer": {"id": customer_id},
    "item_prices": [{"item_price_id": "credit-100-usd", "quantity": 1}],
    "redirect_url": "https://app.example.com/credits/return",
    "pass_thru_content": json.dumps({"sku": "credit-100-usd", "units": 100}),
}).hosted_page
return {"url": hp.url}
```

Webhook handler - grant on `payment_succeeded`, revoke on the reverse events:
```python
CREDIT_SKU_UNITS = {
    "credit-100-usd": 100,
    "credit-500-usd": 500,
    "credit-1000-usd": 1000,
}

def apply_credit_event(event_id, event_type, content):
    if event_type == "payment_succeeded":
        adjust_credits(content["invoice"], sign=+1, event_id=event_id)
    elif event_type in ("payment_refunded", "invoice_voided"):
        adjust_credits(content["invoice"], sign=-1, event_id=event_id)
    elif event_type == "credit_note_created":
        # Refundable or adjustment credit note linked to a previously paid invoice -> revoke.
        cn = content["credit_note"]
        if cn.get("reference_invoice_id"):
            adjust_credits_for_invoice_id(cn["reference_invoice_id"],
                                          amount_minor=cn["amount_refundable"] + cn["amount_adjusted"],
                                          sign=-1, event_id=event_id)

def adjust_credits(invoice, sign, event_id):
    rv = int(invoice["resource_version"])
    customer_id = invoice["customer_id"]
    with db.transaction():
        row = db.fetchone("SELECT resource_version FROM credit_invoices WHERE invoice_id=%s FOR UPDATE",
                          (invoice["id"],))
        if row and rv <= row["resource_version"]:
            return  # stale, drop

        total_units = 0
        for li in invoice.get("line_items", []):
            # Filter: only line items that came from a credit-pack Item Price.
            # entity_type values are documented in references/invoices_billing.md.
            if li.get("entity_type") != "charge_item_price":
                continue
            units = CREDIT_SKU_UNITS.get(li.get("entity_id"))
            if not units:
                continue
            total_units += units * li.get("quantity", 1)

        if total_units == 0:
            return  # invoice contains no credit-pack lines; e.g. a subscription renewal

        db.execute(
            "INSERT INTO credit_ledger(customer_id, invoice_id, event_id, delta_units) "
            "VALUES(%s,%s,%s,%s) ON CONFLICT (event_id) DO NOTHING",
            (customer_id, invoice["id"], event_id, sign * total_units),
        )
        db.execute(
            "INSERT INTO credit_invoices(invoice_id, resource_version) VALUES(%s,%s) "
            "ON CONFLICT (invoice_id) DO UPDATE SET resource_version=EXCLUDED.resource_version",
            (invoice["id"], rv),
        )
```

Why this shape:
- Triggering on `payment_succeeded` (not `invoice_generated`) ensures money actually moved. Source: `references/webhooks_events.md` section 3.
- Filtering line items by `entity_type == "charge_item_price"` and `entity_id in CREDIT_SKU_UNITS` distinguishes a credit-pack purchase from a subscription renewal whose invoice happened to be paid by the same gateway hop. Consolidated invoicing can mix both kinds of lines on a single invoice.
- The ledger insert keyed on `event_id` makes the grant idempotent under Chargebee's 7-attempt retry schedule. The `resource_version` guard makes it safe against out-of-order delivery.
- Revoke on `payment_refunded`, `invoice_voided`, and `credit_note_created` covers the three documented reversal paths.

## 9. Refund flow

Full refund of a paid invoice:
```python
inv = chargebee.Invoice.refund(invoice_id, {
    "comment": "Customer requested refund",
    "customer_notes": "Sorry to see you go.",
})
```

Partial refund:
```python
inv = chargebee.Invoice.refund(invoice_id, {
    "refund_amount": 1500,    # minor units
    "comment": "Partial refund for unused term",
})
```

Refund a specific line item (creates an adjustment credit note then refund):
```python
cn = chargebee.CreditNote.create({
    "reference_invoice_id": invoice_id,
    "total": 1500,
    "type": "refundable",
    "reason_code": "service_unsatisfactory",
    "line_items": [{
        "reference_line_item_id": "li_xxx",
        "unit_amount": 1500,
        "quantity": 1,
    }],
}).credit_note

chargebee.CreditNote.refund(cn.id, {})
```

Resulting transactions flow through the original payment gateway. Verify in the Chargebee admin and the gateway dashboard.
