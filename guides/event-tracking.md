# Event Tracking — Web Pixel consent-aware forwarding

> `/devflow` Step 6 verify: task có cần bắn event không + đặt đúng pattern. Rút từ code thật `cookie-bar/extensions/web-pixel-events/`. ⚙️ = tùy chỉnh.

## 1 · Kiến trúc
Shopify **Web Pixel** extension (`extensions/web-pixel-events/src/index.js`) chạy trong **sandbox**, `register(...)` subscribe **4 commerce events** → gate consent → forward sang pixel từng integration:
- **Meta** `/tr` · **GA4** `/g/collect` · **Pinterest** `/v3` → **client-side** (fetch no-cors, keepalive)
- **TikTok** → **server-side** (qua backend app: client không record được → Events API)

**Settings** gói trong **1 field JSON `config`** (Shopify từ chối field rỗng):
```
{ metaPixelIds, ga4Id, testEventCode, pinterestTagId, tiktok(shopId), apiBase }
```
→ field rỗng = integration đó **off**.

## 2 · Consent-aware (bắt buộc)
`createConsentState(init, customerPrivacy)` (`helpers/consentState.js`) → `getState() → { marketing, analytics }`, cập nhật live qua event `visitorConsentCollected`.
- Meta / Pinterest / TikTok → fire khi **`marketing`** = true
- GA4 → fire khi **`analytics`** = true
- KHÔNG consent → KHÔNG fire. *(đây là điểm khác biệt vs app khác — luôn giữ)*

## 3 · Event mapping (`EVENT_MAP` trong index.js)
| Shopify topic | Meta | GA4 | Pinterest | TikTok |
|---|---|---|---|---|
| `product_viewed` | ViewContent | view_item | viewcontent | ViewContent |
| `product_added_to_cart` | AddToCart | add_to_cart | addtocart | AddToCart |
| `checkout_started` | InitiateCheckout | begin_checkout | initiatecheckout | InitiateCheckout |
| `checkout_completed` | Purchase | purchase | checkout | CompletePayment |

`eventMappers.js` chuẩn hoá payload → `{ value, currency, contentIds, items, eventId }`. **`eventId`** = khoá dedup (Purchase dùng order id ổn định).

## 4 · Forwarder pattern (1 file / integration)
`forwarders/{meta,ga4,pinterest,tiktok}Forwarder.js` — cùng interface `forwardToX(params)`:
- Fetch **no-cors + keepalive**; lỗi **nuốt** (try/catch) — KHÔNG bao giờ làm vỡ trang storefront.
- Meta: 1 fetch / pixel id (concurrent `Promise.all`).

## 5 · Thêm integration mới — checklist
1. `forwarders/<x>Forwarder.js` — hàm `forwardTo<X>(params)` (no-cors, nuốt lỗi)
2. Thêm cột event name vào `EVENT_MAP` (index.js) + nhánh `send<X>` trong `dispatchEvent` (gate consent category đúng)
3. Thêm field vào `config` JSON + đọc/parse trong `register(...)` (`<x>Enabled = …`)
4. Backend (nếu server-side như TikTok): `packages/functions/src/services/integrations/<x>EventsApiService.js` + `controllers/<x>EventController.js` + `helpers/integration/<x>ForwardConfig.js` + route `routes/clientApi.js`
5. Admin: `helpers/integration/buildWebPixelSettings.js` + `const/defaultIntegration.js` + `repositories/integrationRepository.js` + toggle UI (`packages/assets`)
6. Map consent: marketing (ads) hay analytics?

## 6 · Naming / payload
- Pixel event name theo chuẩn từng nền tảng (bảng §3) — KHÔNG tự đặt tên.
- Payload tối thiểu: `value`, `currency`, `contentIds`/`items`, `eventId` (dedup).

## 7 · Test tracking
- Verify event **fire đúng** khi consent ON + **KHÔNG fire** khi consent OFF (test cả 2).
- Meta: `testEventCode` để xem trong Test Events.
- TikTok server-side: check log backend `controllers/<x>EventController.js`.
- ⚙️ Bổ sung cách test riêng của bạn ở đây.
