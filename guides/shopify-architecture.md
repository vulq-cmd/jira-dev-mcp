# Shopify App Architecture

> `/devflow` Step 6 verify: code đặt đúng chỗ chưa + plan đúng layer. Rút từ cấu trúc thật (cookie-bar) + per-app skills. ⚙️ = tùy chỉnh.

## ⭐ DRY — mỗi app đã có `.claude/skills/` riêng
Mỗi app dir có sẵn skill chi tiết theo layer (tự áp khi code trong app đó). **Ưu tiên dùng các skill này thay vì lặp lại ở đây:**
`backend` · `frontend` · `scripttag` · `firestore` · `polaris` · `shopify-api` · `theme-extension` · `security` · `bigquery` · `cloud-tasks` · `redis-caching` · `api-design`
*(withdrawal-forms còn có `langchain`, `shopify-functions`, `storefront-data`)*
→ devflow verify: nếu code thuộc layer nào, dựa skill `<app>:<layer>` để check pattern.

## 1 · Sơ đồ repo (mỗi app = 1 repo riêng)
```
packages/
  functions/   ← backend (Firebase Functions, Node)
  assets/      ← admin React + Polaris (embedded app)
  scripttag/   ← storefront widget (Preact, nhẹ)
extensions/
  theme-app-extension/   ← app embed block (Liquid)
  web-pixel-events/      ← Customer Events tracking (→ event-tracking.md)
shopify.app.toml         ← config app (base: shopify.app.local.toml = local, KHÔNG commit)
```

## 2 · Bảng: loại thay đổi → đặt ở đâu
| Thay đổi | Thư mục |
|---|---|
| API / business logic | `packages/functions/src/{routes,controllers,services,repositories}` |
| UI admin (embedded) | `packages/assets/src/{config,layouts,components,pages}` |
| Widget storefront | `packages/scripttag/src/` |
| Block trên theme khách | `extensions/theme-app-extension/blocks/*.liquid` |
| Tracking pixel/event | `extensions/web-pixel-events/` (+ backend services) |

## 3 · Backend (`packages/functions/src/`)
Layer: **route → controller → service → repository** (+ `middleware`, `handlers`, `commands`, `helpers`, `const`, `config`).
- `routes/` định nghĩa endpoint → `controllers/` điều phối → `services/` business logic → `repositories/` truy cập data (Firestore).
- DB = **Firestore**; analytics = **BigQuery**; cache = **Redis**; job nền = **Cloud Tasks / Pub/Sub**. *(chi tiết: skill `<app>:firestore|bigquery|redis-caching|cloud-tasks|backend`)*
- ❌ Tránh: business logic trong route, gọi Firestore thẳng từ controller (phải qua repository).

## 4 · Frontend admin (`packages/assets/`)
- React + **Polaris** (embedded trong Shopify Admin). Hook data: `useFetchApi/useCreateApi/useEditApi`. *(skill `<app>:frontend|polaris`)*
- **Embedded vs standalone:** `isEmbeddedApp` / `IS_EMBEDDED_APP` — 1 số UI (vd top-bar info-icon) **chỉ render standalone** (ngoài Shopify Admin). Verify đúng môi trường.

## 5 · Storefront & extensions
- `packages/scripttag/` — widget Preact (banner/popup consent), tối ưu bundle size. *(skill `<app>:scripttag`)*
- `extensions/theme-app-extension/` — block Liquid (app embed), JS tối thiểu. *(skill `theme-extension`)*

## 6 · Khác biệt giữa app ⚙️
- **Base branch:** đa số `master`, **withdrawal-forms = `main`** (đọc động `origin/HEAD`).
- Stack cốt lõi giống nhau (functions/assets/scripttag/extensions). Bổ sung riêng theo app → xem `.claude/skills/` của app đó.

## 7 · Đặt SAI chỗ — tránh
- Logic nghiệp vụ nhồi vào route/controller (đúng: service).
- Query DB rải rác (đúng: repository).
- Hardcode secret/config local vào code (dùng env / `shopify.app.local.toml` — KHÔNG commit).
- UI standalone-only mà không gate `isEmbeddedApp`.
