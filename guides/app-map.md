# App Map — Jira task → local app

`/devflow` dùng file này để nhận diện task thuộc app nào, để bạn confirm mà không cần mở Jira.

## PRIMARY signal — title prefix `[Loại][APP]`
Title task theo format: `[<Loại>][<App-viết-tắt>] <mô tả>`
- `<Loại>`: `Dev`, `Support`, … (loại công việc — không dùng để detect app)
- `<App-viết-tắt>`: **đây là khóa detect app** (confidence **HIGH** khi khớp)

| Viết tắt | Tên hiển thị | App dir | Purpose |
|----------|--------------|---------|---------|
| `CB` | **Cookie Bar** | `cookie-bar/` | Cookie consent / privacy bar |
| `AC` | **Accessibility** | `accessibility/` | Accessibility / a11y widget |
| `AV` | **Age Verification** | `age-verification/` | Age verification gate |
| `WF` | **Withdrawal Forms** | `withdrawal-forms/` | Withdrawal / form flows |
| `OL` | **Order Limit** | `order-limit/` | Order quantity/value limits |
| `FF` | **Sea Fraud Filter** | `sea-fraud-filter/` | Fraud filtering |

> **Tên hiển thị** = tên brief in ra (vd "Withdrawal Forms"), KHÔNG in slug dir. Slug chỉ dùng nội bộ để Grep code.
> Cả 6 viết tắt đã xác nhận từ Jira thật (CB/AC/AV/WF/OL/FF).

## Đa app trong 1 prefix — `[Loại][APP1, APP2, ...]`
Title có thể gắn **nhiều app**, phẩy: vd `[DEV][CB, AC, OL]`, `[DEV][OL, AC, CB, AV, FF]`.
→ Detect **tất cả** app khớp → brief hiển thị nhiều app badge + verify/touch-points trên từng app dir. Hỏi dev app nào là trọng tâm nếu cần.

## Không có `[APP]` — chỉ `[Loại]`
Vd `[DEV] improvement: Update User guide link` (không bracket app). Fallback theo thứ tự:
1. **Parent/subtask:** nếu là sub-task → lấy app của task cha; nếu có sub-task gắn `[APP]` → suy ra.
2. **Repo link** trong description (`gitlab.com/avada/<app>`).
3. **Keyword** (bảng dưới).
4. Vẫn không rõ → "app undetected", hỏi dev chọn.

## FALLBACK — keyword (khi title không có prefix `[APP]`)
| App dir | Keyword hints |
|---------|---------------|
| `cookie-bar/` | cookie, consent, gdpr, ccpa, privacy, banner, region, pixel, tracking |
| `accessibility/` | accessibility, a11y, wcag, contrast, screen reader, ada |
| `age-verification/` | age, verify, 18+, birthday, dob, age gate |
| `order-limit/` | order limit, min/max, quantity, cart limit, threshold |
| `sea-fraud-filter/` | fraud, risk, blocklist, chargeback, filter, suspicious |
| `withdrawal-forms/` | withdrawal, form, refund, request, submission |

## Detect order (skill theo thứ tự này)
1. **Title prefix `[APP]`** → map bảng trên → confidence HIGH
2. Keyword trong title/description → confidence MEDIUM
3. Repo link trong description (vd `gitlab.com/avada/<app>`) → HIGH
4. Không khớp → "app undetected", hỏi user chọn

## Notes
- Workspace root: `/Users/avada/Desktop/Workspace/apps`. App dir là con trực tiếp.
- Task có thể đụng >1 app → skill liệt kê tất cả app khớp.
- File này = nguồn chân lý cho detect; thêm app mới thì update bảng prefix.
