# Branch Naming

> `/devflow` suy ra tên branch từ rule này. **Sửa theo ý bạn** (⚙️).

## Pattern ⚙️
```
<type>/<TICKET-KEY>-<slug-ngắn>
```
- `type`: `feature` | `fix` | `hotfix` | `refactor` | `chore`
- `TICKET-KEY`: key Jira, vd `SB-13099`
- `slug`: 2–5 từ, kebab-case, tiếng Anh

## Ví dụ
```
feature/SB-13099-rename-cookie-consent-page
fix/SB-13150-onboarding-step1-preview
```

## Bắt đầu task mới — LUÔN branch từ BASE mới nhất
Base đọc động từ `origin/HEAD` (đa số app = `master`, **withdrawal-forms = `main`**) — KHÔNG hardcode:
```bash
BASE=$(git -C <app> symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@')
git -C <app> checkout "$BASE" && git -C <app> pull
git -C <app> checkout -b <type>/<TICKET-KEY>-<slug>
```
> KHÔNG tách branch từ branch task cũ. Working tree đang bẩn → `git stash`/commit trước, đừng mang thay đổi cũ sang branch mới.

## Quy ước
- Không commit thẳng lên `master`
- 1 branch / 1 ticket (subtask gom chung branch task cha, trừ khi tách riêng)
- Sau khi xong: push branch → tạo MR vào `master`
