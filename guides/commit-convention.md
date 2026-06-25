# Commit Convention

> Đây là rule `/devflow --commit` đọc khi sinh commit message. **Sửa trực tiếp file này theo ý bạn** — chỗ nào đánh dấu ⚙️ là tùy chỉnh cá nhân.

## Format (Conventional Commits)
```
<type>(<scope>): <subject>

<body — optional>

<footer — optional>
```

## type ⚙️
| type | dùng khi |
|------|----------|
| `feat` | thêm tính năng |
| `fix` | sửa bug |
| `refactor` | đổi code không đổi hành vi |
| `perf` | tối ưu hiệu năng |
| `test` | thêm/sửa test |
| `docs` | tài liệu |
| `chore` | config, deps, việc lặt vặt |
| `style` | format, không đổi logic |

## scope ⚙️
- = tên app: `cookie-bar`, `age-verification`, `accessibility`, `order-limit`, `sea-fraud-filter`, `withdrawal-forms`
- hoặc vùng nhỏ hơn: `cookie-bar/banner`, `api`, `theme-extension`

## subject
- tiếng Anh, **imperative** ("add", "fix", không "added/fixes")
- chữ thường đầu câu, **không dấu chấm cuối**, ≤ ~72 ký tự

## body (khi cần)
- giải thích **what + why**, không phải how
- xuống dòng, mỗi ý 1 dòng

## footer — gắn ticket ⚙️
- `Refs: SB-1234` (mặc định) — hoặc bạn muốn để key ngay subject thì đổi ở đây
- breaking change: `BREAKING CHANGE: <mô tả>`

## Bắt buộc
- ❌ **Không** có reference tới AI/Claude trong message
- ✅ Commit gọn, chỉ chứa thay đổi thật của task
- ✅ Lint trước commit, test trước push

## Ví dụ
```
feat(cookie-bar): add 6 US state privacy regions to consent bar

Adds CA, VA, CO, CT, UT region detection + per-region default toggles.

Refs: SB-13099
```
```
fix(age-verification): prevent gate flash on cached storefront load

Refs: SB-13150
```

## ⚙️ Ghi chú cá nhân của bạn
<!-- viết thêm quy ước riêng ở đây, vd: luôn 1 commit / 1 subtask, ngôn ngữ, emoji... -->
