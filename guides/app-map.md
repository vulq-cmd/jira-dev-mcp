# App Map — Jira task → local app

`/devflow` uses this to detect which app a ticket belongs to, so you confirm
without opening Jira. Match order: **Jira project key → component → label →
title/description keyword**. First strong match wins; if ambiguous, the skill
lists candidates and asks.

> ACTION REQUIRED: fill the `Jira project` / `Components` columns with your real
> values (run `jira_get_fields` + open one ticket per app to see them). Keywords
> are pre-seeded; tune as needed.

| App dir | Purpose | Jira project | Components | Keyword hints |
|---------|---------|--------------|------------|---------------|
| `accessibility/` | Accessibility / a11y widget | _TODO_ | _TODO_ | accessibility, a11y, wcag, contrast, screen reader, ada |
| `age-verification/` | Age verification gate | _TODO_ | _TODO_ | age, verify, 18+, birthday, dob, age gate |
| `cookie-bar/` | Cookie consent / privacy bar | _TODO_ | _TODO_ | cookie, consent, gdpr, ccpa, privacy, banner, region |
| `order-limit/` | Order quantity/value limits | _TODO_ | _TODO_ | order limit, min/max, quantity, cart limit, threshold |
| `sea-fraud-filter/` | Fraud filtering | _TODO_ | _TODO_ | fraud, risk, blocklist, chargeback, filter, suspicious |
| `withdrawal-forms/` | Withdrawal / form flows | _TODO_ | _TODO_ | withdrawal, form, refund, request, submission |

## Notes
- Workspace root: `/Users/avada/Desktop/Workspace/apps`. App dirs are direct children.
- A ticket may touch >1 app (shared component / cross-app banner) → skill reports all matched apps.
- If no match: skill says "app undetected" and asks you to pick, rather than guessing.
- Keep this file the single source of truth for detection; update when a new app is added.
