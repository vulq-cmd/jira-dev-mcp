# Testing Checklist

> `/devflow` Step 6 + `--tests` dùng. Phản ánh thực tế: app chủ yếu **manual + browser test** (skill `shopify-testing`), unit test formal ít. ⚙️ = tùy chỉnh.

## Trước khi chuyển "Waiting To Test"
- [ ] **Lint** pass · **build** pass
- [ ] Self-review diff: chỉ file thuộc task (không lẫn package/lock/.env/local config)

## Manual verify (theo loại task)
- [ ] **Admin (embedded)** — trong Shopify Admin: chức năng đúng
- [ ] **Admin (standalone)** — ngoài Admin (`IS_EMBEDDED_APP=false`): UI standalone-only (vd top-bar info-icon) đúng
- [ ] **Storefront** — widget/banner/popup hiển thị + hành vi đúng
- [ ] **Mobile** — responsive, không bị che/lỗi layout *(nhiều bug cũ là mobile)*
- [ ] Edge case nêu trong ticket / ảnh mockup

## Task tracking (event forwarding) — bắt buộc test 2 chiều
- [ ] Consent **ON** → event **fire** (Meta test code / GA4 DebugView / log backend)
- [ ] Consent **OFF** → event **KHÔNG** fire
- [ ] Đúng event mapping (xem `event-tracking.md` §3)

## Browser / e2e
- [ ] Dùng skill **`shopify-testing`** (Playwright/browser) cho flow chính *(withdrawal-forms)*
- [ ] `/ck-scenario` sinh edge case nếu task phức tạp

## Không hồi quy
- [ ] Chức năng cũ liên quan vẫn chạy
- [ ] Test cũ (nếu có, vd `packages/functions/src/test`) không vỡ

## ⚙️ Bổ sung của bạn
<!-- coverage tối thiểu, app cụ thể cần test gì... -->
