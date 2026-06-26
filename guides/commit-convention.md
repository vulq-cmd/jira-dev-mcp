# Commit Convention

> Rule `/devflow --commit` đọc khi sinh commit. Rút từ git history thật của repo. ⚙️ = tùy chỉnh.

## Format
```
<type>(<scope>): <subject> (<TICKET-KEY>)
```
- **Mã task BẮT BUỘC** ở cuối subject, trong ngoặc: `(SB-13189)`.
- 1 dòng subject là đủ cho task nhỏ; body optional cho task lớn.

## type
`feat` · `fix` · `chore` · `refactor` · `revert` · `perf` · `docs` · `test` · `style`

## scope ⚙️
- = **module/khu vực trong app**, KHÔNG phải tên app (repo đã là 1 app rồi).
- Ví dụ thật: `integrations`, `region`, `banner`, `onboarding`, `web-pixel`, `translations`.
- Có thể bỏ scope nếu thay đổi chung: `fix: ...`.

## subject
- Tiếng Anh, **imperative** ("add", "fix"; không "added/fixes")
- chữ thường, **không dấu chấm cuối**, ≤ ~72 ký tự (chưa tính `(KEY)`)

## body (khi cần)
- giải thích **what + why**, không phải how; mỗi ý 1 dòng
- `BREAKING CHANGE: <mô tả>` nếu có

## Bắt buộc
- ✅ **Mã task** luôn có trong message `(SB-XXXX)`
- ❌ KHÔNG reference AI/Claude
- ✅ Commit gọn, chỉ thay đổi thật của task · lint trước commit, test trước push

## Ví dụ *(từ history thật)*
```
feat(region): add 6 US states to recommended privacy list (SB-13189)
fix(integrations): support multiple Meta pixel IDs in web pixel forwarding (SB-9927)
chore: bump @avada/app-widget-hook 0.0.15 → 0.0.24 (SB-XXXX)
```
Task lớn (có body):
```
feat(integrations): add consent-aware web pixel event forwarding (SB-9927)

Forward Shopify Customer Events (AddToCart, Purchase) to Meta + GA4,
gated by visitor consent category. Phase 1 of tracking-data improvement.
```

## Staging (git add) — CHỈ stage file thuộc task

> Mỗi app = 1 repo riêng → luôn `git -C <app>`. Base đọc động từ `origin/HEAD` (đa số `master`, **withdrawal-forms = `main`**) — KHÔNG hardcode.

**Nguyên tắc:**
- TUYỆT ĐỐI KHÔNG `git add .` / `-A` / add thư mục rộng. Chỉ add path đích danh lấy từ **"File sẽ sửa"** trong 🛠 Hướng giải quyết.
- Add tách pathspec bằng `--`: `git -C <app> add -- "src/My Folder/file.vue"`.
- KHÔNG commit/push thẳng base — chỉ commit trên branch task.

**Loại trừ mặc định (KHÔNG stage dù có trong diff):**
- `package.json` / `yarn.lock` / `package-lock.json` / `pnpm-lock.yaml` đổi do install local *(dấu hiệu: package.json +3/-1 kèm yarn.lock +329/-181)*
- `*.local.toml` (`shopify.app.local.toml`), `.firebaserc`, dev scripts, file setup local, `plans/`, `.claude/settings.local.json`
- Build/generated: `dist/`, `build/`, `coverage/`, `*.min.js`, `*.log`, `.DS_Store`, `node_modules`
- Mọi `.env*` + secret (`*.pem`, `*.key`, `credentials.json`)
- → Chỉ stage lockfile khi task **chủ đích bump deps**: stage `package.json` + lockfile cùng nhau, commit riêng `chore(deps): … (SB-XXXX)`, HỎI dev trước.

**Quy trình (show → confirm → add từng file → verify):**
```bash
git -C <app> status -sb        # xác nhận đúng branch task (KHÔNG phải base)
# → IN danh sách SẼ stage + danh sách BỎ QUA (kèm lý do) → CHỜ dev confirm
git -C <app> add -- src/components/NewBanner.vue packages/functions/src/x.js
git -C <app> diff --cached --name-only      # verify đúng phạm vi
git -C <app> diff --cached --name-only | grep -iE '\.env|secret|credential|\.pem|\.key'   # secret → STOP
```

**Case đặc biệt:**
- File mới (`??`): add path tường minh, list bằng `git -C <app> ls-files --others --exclude-standard`
- File lẫn task + non-task: `git -C <app> add -p <path>` (y=task, n=bỏ)
- Rename: stage cả old+new, check `diff --cached --stat -M`
- Lỡ `git add .`: gỡ nhiễu `git -C <app> restore --staged <path>` (giữ nội dung)
- Revert nhiễu lock về base: `git -C <app> checkout -- yarn.lock package.json`

## ⚙️ Ghi chú cá nhân
<!-- quy ước riêng: 1 commit/subtask, ... -->
