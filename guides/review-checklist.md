# Review Checklist

> `/devflow --review` (và `/code-review`) dùng list này. **Sửa/thêm/bớt theo ý bạn** (⚙️). Đánh ✅/⚠️/❌ cho từng mục.

## 1. Đúng requirement
- [ ] Code làm đúng **acceptance criteria** của ticket (so với brief đã confirm)
- [ ] Đúng **app**, đúng chỗ (theo `shopify-architecture.md`)
- [ ] Cover edge case nêu trong ticket / ảnh mockup

## 2. Shopify-specific ⚙️
- [ ] Không vượt **API rate limit**; dùng bulk/pagination khi cần
- [ ] Theme app extension / block đúng chuẩn, không phá theme khách
- [ ] Webhook/billing (nếu có) idempotent, verify HMAC
- [ ] Tương thích đa storefront / đa ngôn ngữ (i18n) nếu task yêu cầu

## 3. Bảo mật
- [ ] Không hardcode secret/token/API key
- [ ] Validate + sanitize input; tránh XSS/injection
- [ ] Phân quyền đúng (shop scope, không lộ data shop khác)

## 4. Hiệu năng
- [ ] Không N+1 query / loop gọi API thừa
- [ ] Không block render storefront (script defer/async)
- [ ] Payload/bundle không phình

## 5. Event tracking ⚙️
- [ ] Có event cần bắn theo `event-tracking.md`? Đặt đúng tên + payload?

## 6. Test
- [ ] Có test cho path chính + edge case (theo `testing-checklist.md`)
- [ ] Test cũ không vỡ

## 7. Code quality / convention
- [ ] Đặt tên rõ, file < ~200 dòng (tách module nếu quá)
- [ ] Không code chết / console.log thừa
- [ ] Commit theo `commit-convention.md`, branch theo `branch-naming.md`

## ⚙️ Tiêu chí riêng của bạn
<!-- thêm rule review cá nhân ở đây -->
