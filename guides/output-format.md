# Output Format — `/devflow` Dev Brief

> **Nguồn chân lý.** Mọi brief `/devflow` in ra terminal PHẢI theo file này. Sửa format thì sửa ở đây; SKILL.md chỉ trỏ về đây.

Brief in ra Claude Code TUI (GitHub-flavored markdown — KHÔNG HTML, không màu). Dev đọc để hiểu task + duyệt hướng làm mà **không mở Jira**.

---

## 1 · Nguyên tắc

- **Cô đọng mà đủ chi tiết** — gạch đầu dòng, KHÔNG viết đoạn dài. Mỗi ý 1 dòng.
- **Mã task nổi bật** (H1) + tiêu đề **đã bỏ prefix `[Loại][APP]`** (app hiển thị riêng ở badge).
- **App = tên hiển thị đầy đủ** (vd "Withdrawal Forms"), KHÔNG in slug `withdrawal-forms`. (slug chỉ dùng nội bộ Grep — xem `app-map.md`.)
- **KHÔNG** ghi dòng "khớp bởi signal…" — title đã có `[APP]`, dev biết rồi.
- **Adaptive — chỉ hiện section CÓ nội dung.** Task nhỏ → ngắn; task lớn → tự thêm Scope / Liên quan / Hình ảnh / Rủi ro. Đừng nhồi section rỗng.
- **Requirement để NGUYÊN VĂN** (giữ bảng nếu ticket có bảng), bọc `> blockquote`. "Cách hiểu của tôi" là restatement riêng — để dev soi hiểu sai.
- **Flow = TREE dạng nested bullet list** khi có chuỗi (data/render flow). Thụt lề = chiều flow, mỗi node 1 dòng ngắn → tự wrap, **KHÔNG scroll ngang**. TUYỆT ĐỐI không nhét cả chuỗi vào 1 dòng / code block dài.
- **2 cổng (bắt buộc):** 🟠 Cần confirm (nếu còn mơ hồ) + 🔒 Hướng giải quyết (phải confirm TRƯỚC KHI code).
- Không bịa → `—`. Không dump JSON thô.

---

## 2 · Bộ icon (KHÓA CỨNG — chỉ dùng 2 bảng này, mỗi icon đúng 1 nghĩa)

**Icon đầu mục** *(mỗi section đúng 1 icon)*

| Icon | Section |
|---|---|
| 🎫 | Header / mã task |
| 📦 | App |
| 📋 | Requirement |
| 🎯 | Scope |
| 📂 | Touch-points |
| 🔗 | Liên quan |
| 💡 | Cách hiểu của tôi |
| 🖼 | Hình ảnh |
| 🚦 | Độ rõ ràng |
| 🛠 | Hướng giải quyết |
| 🚨 | Rủi ro |
| 🔄 | Tiến độ *(chỉ khi task Doing)* |

**Chấm trạng thái (status dot)** — màu = mức độ (traffic-light), dùng inline

| Dot | Nghĩa |
|---|---|
| 🟢 | Đã rõ / sẵn sàng / đạt / confidence HIGH |
| 🟠 | Cần confirm / chú ý / confidence MED |
| 🔴 | Blocker / chưa rõ / rủi ro cao / confidence LOW |
| 🔒 | Cổng — confirm trước khi code |
| ✓ / ✗ | Trong / ngoài scope |
| ◂ | parent (sub-task của) |

> Trạng thái LUÔN dùng chấm tròn màu **🟢🟠🔴** — KHÔNG dùng 🟢/🟠. KHÔNG dùng emoji ngoài 2 bảng. Rủi ro section = 🚨 (icon đầu mục); mức rủi ro từng dòng = 🔴/🟠.

---

## 3 · Template chuẩn

```markdown
# 🎫 <TICKET-KEY> — <tiêu đề, bỏ prefix [Loại][APP]>
> <🟠 Cần confirm <N> điểm trước khi code  |  🟢 Đã rõ — sẵn sàng implement>
> 📦 App **<Tên hiển thị>** · <Type>< ◂ PARENT-KEY nếu sub-task> · <Status> · <Priority>

📋 **REQUIREMENT** *(nguyên văn)*
> <Mục tiêu / câu quote nguyên văn>
<bảng tiêu chí nghiệm thu nếu ticket có bảng>
- <ghi chú nguyên văn, mỗi ý 1 dòng>

🎯 **SCOPE** *(chỉ hiện nếu ticket phân định)*
- ✓ Trong: <…>
- ✗ Ngoài: <…>

📂 **TOUCH-POINTS** *(flow tree — thụt lề = chiều flow)*
- 🔸 `<path:line>` — `<symbol>` ← <vai trò / điểm sửa>
  - → `<path:line>` — `<symbol>` <vai trò / chỉ verify>
    - → `<path:line>` — <điều kiện / kết quả>
- _(nếu các file ĐỘC LẬP, không thành chuỗi → list phẳng, không thụt lề)_

🔗 **LIÊN QUAN** *(chỉ hiện nếu có)*
- MR/commit · plan/ticket · prior art

💡 **CÁCH HIỂU CỦA TÔI**
- <sẽ build gì — gồm cả điều chỉ thấy trong ảnh>
- <ràng buộc / vì sao gói gọn đúng scope>

🖼 **HÌNH ẢNH** *(chỉ hiện nếu có ảnh)*
- `<file>` → <cho thấy / ngụ ý>

🚦 **ĐỘ RÕ RÀNG**
> <🟢 Đã rõ — không điểm cần confirm  |  🟠 Cần confirm — chặn trước khi code:>
- <điểm cần confirm + khuyến nghị của tôi>   ← chỉ khi 🟠

🛠 **HƯỚNG GIẢI QUYẾT** 🔒 *confirm trước khi code*
- <bước — file: `<path:line>`>
- **Sửa:** `<path:line>` · **Không đụng:** `<vùng>`
- **Setup** *(To Do — base động `$BASE`=origin/HEAD)*: `git checkout $BASE && git pull` → `git checkout -b <type>/<KEY>-<slug>`
- **Commit:** `<type>(<scope>): <subject> (<KEY>)` *(mã task bắt buộc ở cuối)*

🚨 **RỦI RO** *(chỉ hiện nếu có)*
- <edge case / cảnh báo / ảnh hưởng phụ>

**Confirm hướng giải quyết để bắt đầu implement.** *(còn 🟠 ở Độ rõ ràng → trả lời điểm đó trước)*
```

---

## 4 · Ví dụ render (SB-13460)

```markdown
# 🎫 SB-13460 — Cập nhật user guide link sang docs.avada.io
> 🟠 Cần confirm 1 điểm trước khi code
> 📦 App **Withdrawal Forms** · Sub-task ◂ SB-13454 · To Do · Low

📋 **REQUIREMENT** *(nguyên văn)*
> Cập nhật user guide link sang docs.avada.io (Falcon repo `pages/avada-eu-withdrawal-form`). Dev sửa — Tester verify không 404.

| Vị trí | Link mới | Nút |
|---|---|---|
| Top bar góc phải — chỉ standalone | `https://docs.avada.io/avada-eu-withdrawal-form` | icon "i" |
- Link `{{docLink}}` chỉ render standalone (`IS_EMBEDDED_APP=false`) → verify ở standalone, không phải Shopify Admin.

🎯 **SCOPE**
- ✓ Trong: link info-icon "i" top-bar standalone
- ✗ Ngoài: footer "Created by Avada" · Joy/Judgeme (cross-app) · bản embedded

📂 **TOUCH-POINTS** *(flow tree)*
- 🔸 `menuLink.js:1` — `docLink` ← **đổi value** *(điểm sửa duy nhất)*
  - → `AppTopBar.js:50` — `<Button url={docLink}>` *(info-icon "i", chỉ verify)*
    - → `App.js:85` — `isEmbeddedApp=false` ⟹ render **standalone**

💡 **CÁCH HIỂU CỦA TÔI**
- Đổi 1 dòng `docLink` → URL mới
- Biến chỉ dùng bởi info-icon standalone → tự giới hạn scope, không lan embedded
- Footer / cross-app links: không đụng

🚦 **ĐỘ RÕ RÀNG**
> 🟠 Cần confirm — chặn trước khi code:
- Đổi qua hằng `docLink` (khuyến nghị) hay hardcode URL trong `AppTopBar.js`?

🛠 **HƯỚNG GIẢI QUYẾT** 🔒 *confirm trước khi code*
- `menuLink.js:1` → `docLink = 'https://docs.avada.io/avada-eu-withdrawal-form'`
- Verify info-icon top-bar standalone trỏ đúng, không 404
- **Sửa:** `menuLink.js:1` · **Không đụng:** `AppTopBar.js`, footer, appList
- **Setup** *(withdrawal-forms base = `main`)*: `git checkout main && git pull` → `git checkout -b feature/SB-13460-update-userguide-link`
- **Commit:** `fix(menu): update user guide link to docs.avada.io (SB-13460)`

🚨 **RỦI RO**
- Grep `docLink` toàn app trước khi đổi (hiện 1 nơi → an toàn)
- URL mới phải tồn tại trên docs.avada.io (tránh 404)

**Confirm hướng giải quyết để bắt đầu implement.** *(trả lời điểm Cần confirm ở Độ rõ ràng trước)*
```

---

## 5 · Section 🔄 TIẾN ĐỘ — chỉ hiện khi task = **Doing** (RESUME)

Khi ticket status = `Doing` → thêm section **🔄 TIẾN ĐỘ ngay sau header** (trước Requirement). Mọi thứ suy ra **TỪ GIT THẬT**, không đoán. Base động: `BASE=$(git -C <app> symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@')`.

**Thành phần:**
- **Branch** đang resume + ahead/behind vs base (`git -C <app> rev-list --left-right --count $BASE...<branch>`)
- **Commit đã làm** (`git -C <app> log --oneline $BASE..<branch>`)
- **Uncommitted** (`git -C <app> status -sb`, `diff --stat`) + stash (`stash list`)
- **Tiêu chí nghiệm thu → trạng thái** (đối chiếu log+diff với "File sẽ sửa"/yêu cầu): 🟢 đã làm · 🟠 đang dở · 🔴 chưa làm, kèm CĂN CỨ git
- **Cảnh báo base chạy xa:** branch behind base → gợi ý rebase/merge, dry-run conflict, chỉ chạy khi dev OK

**Ví dụ:**
```markdown
🔄 **TIẾN ĐỘ** — Doing
- **Branch:** `feat/consent-aware-event-forwarding` (ahead 4 · behind 0 vs master)
- **Commit đã làm:**
  - `a1b2c3d` feat(integrations): add tiktok forwarder skeleton (SB-13408)
  - `e4f5g6h` feat(integrations): wire consent gate to forwarder (SB-13408)
- **Đang dở (uncommitted):**
  - `M` `…/controllers/tiktokEventController.js` (unstaged)
  - `??` `…/services/tiktokForwarder.js` (untracked)
- **Tiêu chí nghiệm thu → trạng thái:**
  - 🟢 Tạo forwarder service → `tiktokForwarder.js` (commit a1b2c3d)
  - 🟠 Gate event theo consent → `tiktokEventController.js` đang sửa, chưa commit
  - 🔴 Unit test forwarder → chưa thấy file test
```
> Sau 🔄 TIẾN ĐỘ → tiếp tục commit bằng **selective staging** ngay trên branch đang dở (KHÔNG checkout base, KHÔNG tạo branch mới).
