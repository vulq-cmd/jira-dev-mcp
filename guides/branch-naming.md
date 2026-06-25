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

## Quy ước ⚙️
- branch tách từ: `main` hay `dev`? → ⚙️ điền nhánh gốc của bạn
- không commit thẳng lên `main`/`master`
- 1 branch / 1 ticket (subtask gom chung branch của task cha, trừ khi tách riêng)
