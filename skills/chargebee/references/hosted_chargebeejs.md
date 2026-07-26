# Hosted Pages, Chargebee.js, Mobile SDKs

Reference for the customer-facing surfaces. Load when designing checkout, building a self-serve portal, embedding a payment form, or handling 3DS on the client.

## Table of contents

1. Decision matrix
2. Hosted Pages
3. Chargebee.js Drop-In
4. Chargebee.js Components (custom UI)
5. Hosted Portal (Customer Portal)
6. Mobile SDKs
7. PCI scope summary
8. 3DS / SCA on the client

## 1. Decision matrix

Pick the lowest-cost pattern that satisfies UX and PCI requirements.

| Pattern | PCI scope | Customisation | Engineering cost | Use when |
|---|---|---|---|---|
| Hosted Checkout (full redirect) | SAQ-A | Branding only | Lowest | Internal, MVP, low-touch |
| Drop-In on your domain | SAQ-A | Layout + theme | Low | Default for most SaaS |
| Components (custom UI with cbCard fields) | SAQ-A | Full control of form | Medium | Strong design needs |
| Direct API with own form + own gateway token | SAQ-D | Anything | High | Specialised flows only |

## 2. Hosted Pages

Endpoint: `https://{site}.chargebee.com/api/v2/hosted_pages`

Reference: <https://apidocs.chargebee.com/docs/api/hosted_pages>

### Types

- `checkout_new` / `checkout_new_for_items`: new subscription.
- `checkout_existing` / `checkout_existing_for_items`: modify existing subscription.
- `checkout_one_time` / `checkout_one_time_for_items_charges`: ad-hoc charge.
- `manage_payment_sources`: update payment instruments.
- `collect_now`: pay outstanding invoices.
- `update_payment_method`, `update_card`: legacy variants.
- `extend_subscription`: customer-driven extension.
- `accept_quote`: present a quote for acceptance.
- `pre_cancel`: retention page before cancellation completes.
- `view_voucher`: display offline payment voucher (e.g. Boleto).

### State machine

```
created -> requested -> succeeded -> acknowledged
                     \-> cancelled
```

`acknowledged` is set after your backend has acted on the outcome. Use the `acknowledge` API to mark completion.

### Key fields

- `id`, `type`, `state`.
- `url`: secure URL, max 250 chars.
- `embed`: bool; if true, use Chargebee.js to mount inside your page.
- `expires_at`: checkouts expire in **3 hours**; `collect_now` and `manage_payment_sources` expire in **5 days**.
- `redirect_url`: where Chargebee sends the customer after completion.
- `pass_thru_content`: opaque metadata, up to 2048 chars (your tracking ids, return URL, etc.).
- `business_entity_id`: ties the page to a business entity.
- `layout`: `full_page` or `in_app`.

### Backend pattern

```python
hp = chargebee.HostedPage.checkout_new_for_items({
    "subscription_items": [{"item_price_id": "pro-monthly-usd", "quantity": 1}],
    "customer": {"email": "alice@example.com"},
    "redirect_url": "https://app.example.com/checkout/return",
    "pass_thru_content": json.dumps({"order_id": "o_42"}),
})
return {"url": hp.hosted_page.url, "id": hp.hosted_page.id}
```

On `redirect_url`, fetch `hosted_pages/{id}` to confirm `state=succeeded`, then `acknowledge`.

## 3. Chargebee.js Drop-In

Docs: <https://www.chargebee.com/checkout-portal-docs/dropIn-overview.html>

Drop-In is the embeddable checkout that runs in your page via Chargebee.js. You generate it from the Chargebee UI per item_price.

### Init

```html
<script src="https://js.chargebee.com/v2/chargebee.js"
        data-cb-site="acme-test"></script>
<a href="javascript:void(0)"
   data-cb-type="checkout"
   data-cb-item-0="pro-monthly-usd"
   data-cb-item-0-quantity="1">Subscribe</a>
```

### Callbacks

```js
const cb = Chargebee.getInstance();
cb.setCheckoutCallbacks(cart => ({
  loaded: () => { /* iframe loaded */ },
  success: (hostedPageId) => {
    fetch("/checkout/complete", {
      method: "POST",
      body: JSON.stringify({ hosted_page_id: hostedPageId }),
    });
  },
  close: () => { /* user closed without completing */ },
  step: (step) => { /* progress */ },
}));
```

Features: pricing table, personalised offers, cancel page, 3DS helper (handled internally for Drop-In), payment method helper, addon management.

## 4. Chargebee.js Components (custom UI)

Docs: <https://www.chargebee.com/checkout-portal-docs/api-integration-overview.html>

Use Components when Drop-In is too rigid but you still want tokenised, PCI-light cards.

### Init

```html
<script src="https://js.chargebee.com/v2/chargebee.js"></script>
<script>
  const chargebee = Chargebee.init({ site: "acme-test", publishableKey: "pk_test_xxx" });
  const cardComponent = chargebee.createComponent("card");
  cardComponent.createField("number").at("#card-number");
  cardComponent.createField("expiry").at("#card-expiry");
  cardComponent.createField("cvv").at("#card-cvv");
  cardComponent.mount();
</script>
```

### Tokenise

```js
const result = await cardComponent.tokenize();
// result.token -> send to your backend
```

### 3DS

```js
const intent = await fetch("/payment-intent", { method: "POST" }).then(r => r.json());
const authorized = await chargebee.handleCardPayment(intent);
// authorized.id -> consume on backend
```

### Backend

```python
ps = chargebee.PaymentSource.create_using_payment_intent({
    "customer_id": "cust_123",
    "payment_intent": {"id": authorized_intent_id},
})
sub = chargebee.Subscription.create_with_items("cust_123", {
    "subscription_items": [{"item_price_id": "pro-monthly-usd"}],
    "payment_source_id": ps.payment_source.id,
})
```

## 5. Hosted Portal (Customer Portal)

Endpoint: `https://{site}.chargebee.com/api/v2/portal_sessions`

A self-serve area where customers manage subscriptions, invoices, payment methods.

### Flow

```python
session = chargebee.PortalSession.create({"customer": {"id": "cust_123"}})
return session.portal_session.access_url
```

Open the URL in browser, or via Chargebee.js:

```js
cb.setPortalSession(() => fetch("/portal-session").then(r => r.json()));
cb.createChargebeePortal().open({
  subscriptionChanged: (data) => { /* refresh local state */ },
  paymentSourceUpdate: (data) => { /* ... */ },
});
```

Session lifetime: short (typically 1 hour). Refresh on demand.

## 6. Mobile SDKs

Docs: <https://www.chargebee.com/checkout-portal-docs/mobile-solutions-overview.html>

Native iOS and Android SDKs wrap:
- Tokenisation of cards.
- 3DS handling.
- Apple Pay and Google Pay.
- In-App Subscription billing on iOS (StoreKit) and Android (Play Billing) with Chargebee sync.

For React Native and Flutter, official wrappers exist; check the GitHub org: <https://github.com/chargebee>.

## 7. PCI scope summary

- Drop-In and Components mount card fields inside Chargebee-controlled iframes. Card data never touches your DOM or backend. Scope is SAQ-A.
- Hosted Pages redirect off your domain. Scope is SAQ-A.
- If you accept raw card data on your form and send to Chargebee server-side, scope is SAQ-D and you need an SAQ-D-validated processor and quarterly external scans. Avoid.

## 8. 3DS / SCA on the client

3DS is mandatory for EEA and many other regions. Chargebee.js handles the challenge.

Drop-In: built-in. The Drop-In modal shows the 3DS challenge and resolves the `payment_intent` automatically.

Components: explicit call.
```js
const intent = await fetch("/intent").then(r => r.json());
const result = await chargebee.handleCardPayment(intent);
// result.status === "authorized"
```

Helper: `chargebee.handle3DSPayment(intent)` for non-card 3DS flows on supported gateways.

After authorisation, the backend consumes the `payment_intent.id` exactly once. Retries must create a new intent.
