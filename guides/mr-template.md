# MR Template

> `/devflow --mr` dùng để sinh mô tả Merge Request. Target = base branch của app (`master`, withdrawal-forms `main`). ⚙️ = tùy chỉnh.

## Tiêu đề MR
Giống commit chính: `<type>(<scope>): <subject> (SB-XXXX)`

## Mô tả MR (template)
```markdown
## 🎫 Ticket
[SB-XXXX](<link Jira>) — <tiêu đề>

## 🎯 Mục tiêu
<1–2 dòng: làm gì, vì sao>

## 🔧 Thay đổi
- <thay đổi 1 — file/khu vực>
- <thay đổi 2>

## 🧪 Test plan
- [ ] <bước verify 1 — môi trường: standalone/embedded/storefront>
- [ ] <bước 2>
- [ ] Không vỡ chức năng cũ liên quan

## 🖼 Screenshot / Video
<ảnh before/after hoặc video demo — nếu UI>

## ⚠️ Rủi ro / Rollback
- Rủi ro: <…>  ·  Rollback: revert MR / <cách khác>

## ✅ Checklist
- [ ] Lint pass · build pass
- [ ] Self-review diff (chỉ file thuộc task — không lẫn package/lock/.env)
- [ ] Commit theo convention + có mã task (SB-XXXX)
```

## Quy ước ⚙️
- Target branch = base động của app (KHÔNG hardcode master).
- 1 MR / 1 ticket (hoặc theo phase nếu task lớn).
- Reviewer: ⚙️ điền team/người review của bạn.
- Không merge khi pipeline đỏ / chưa được approve.
