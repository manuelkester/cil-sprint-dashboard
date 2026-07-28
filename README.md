# CIL Sprint Team Dashboard

Live dashboard for CIL active sprint tickets, grouped by team.
Published via GitHub Pages — data auto-refreshes every hour via GitHub Actions.

## Setup (one-time)

1. Go to **Settings → Secrets and variables → Actions** and add:

   | Secret | Value |
   |---|---|
   | `JIRA_BASE_URL`  | `https://sisu-agile.atlassian.net` |
   | `JIRA_EMAIL`     | your Atlassian account email |
   | `JIRA_API_TOKEN` | your Jira API token (from id.atlassian.com/manage-profile/security/api-tokens) |

2. Go to **Settings → Pages**, set Source to **Deploy from a branch**, branch `main`, folder `/ (root)`.

3. Click **Actions → Refresh Jira Data → Run workflow** for the first live fetch.

## Refresh button

The Refresh button dispatches the GitHub Actions workflow via the GitHub API,
polls for completion, and auto-reloads `data/*.json` when done (~60 s).

To authenticate the button, run this once in the browser console and it persists across sessions:

```js
localStorage.setItem('gh_token', 'github_pat_...')
```

Generate a fine-grained PAT at **github.com → Settings → Developer settings → Fine-grained tokens**
with `Actions: Read and write` permission scoped to this repo.

## Auto-schedule

The workflow also runs on `cron: "0 * * * *"` (every hour) so the data stays fresh without any manual action.
