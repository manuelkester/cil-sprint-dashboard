"""
Fetches all CIL active sprint tickets from Jira and writes data/ JSON files.
Runs as a GitHub Actions workflow step.
Required env vars: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
"""
import os, json, base64, urllib.request, urllib.parse
from datetime import datetime, timezone

BASE_URL  = os.environ["JIRA_BASE_URL"].rstrip("/")
EMAIL     = os.environ["JIRA_EMAIL"]
API_TOKEN = os.environ["JIRA_API_TOKEN"]

CREDS = base64.b64encode(f"{EMAIL}:{API_TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {CREDS}", "Accept": "application/json"}

JQL       = 'project = CIL AND sprint in openSprints() ORDER BY created DESC'
FIELDS    = "summary,status,issuetype,assignee,customfield_10600,customfield_10006,created"
PAGE_SIZE = 100

def jira_get(path, params=None):
    url = f"{BASE_URL}/rest/api/3/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as r:
        return json.loads(r.read().decode())

def bucket(s):
    s = s or ""
    if s in ("Done","Closed"): return "done"
    if s in ("In Progress","QA In Progress","AI-Generation In Progress"): return "inProgress"
    if s in ("In Code Review","Waiting For Merge","IN Integration","In Validation",
             "Deploy to QA","Deploy to UAT","Ready for Prod","IN PREVALIDATION"): return "inReview"
    if s in ("AI-Generation Done","To Auto-Generate"): return "aiGenDone"
    return "todo"

def active_sprint(sprints):
    for sp in (sprints or []):
        if isinstance(sp, dict) and sp.get("state") == "active":
            return sp.get("name", "")
    return ""

all_issues, start = [], 0
while True:
    data   = jira_get("search", {"jql": JQL, "fields": FIELDS, "startAt": start, "maxResults": PAGE_SIZE})
    issues = data.get("issues", [])
    all_issues.extend(issues)
    start += len(issues)
    print(f"  fetched {start}/{data.get('total',0)}")
    if start >= data.get("total", 0) or not issues:
        break

team_map, ticket_list = {}, []
for issue in all_issues:
    f          = issue["fields"]
    status     = f.get("status", {}).get("name", "")
    team_obj   = f.get("customfield_10600") or {}
    team_name  = (team_obj.get("name","") if isinstance(team_obj, dict) else str(team_obj)) or "No Team"
    sprint     = active_sprint(f.get("customfield_10006"))
    created    = (f.get("created","") or "")[:10]
    b          = bucket(status)
    if team_name not in team_map:
        team_map[team_name] = {"team":team_name,"sprint":sprint,"total":0,"todo":0,"inProgress":0,"inReview":0,"aiGenDone":0,"done":0}
    tm = team_map[team_name]
    tm["total"] += 1; tm[b] += 1
    if sprint and not tm["sprint"]: tm["sprint"] = sprint
    assignee = (f.get("assignee") or {}).get("displayName","")
    ticket_list.append({"key":issue["key"],"summary":f.get("summary",""),"type":(f.get("issuetype") or {}).get("name",""),"status":status,"assignee":assignee,"team":team_name,"sprint":sprint,"created":created})

teams_list = sorted(team_map.values(), key=lambda x: -x["total"])
meta = {"updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"), "total": len(ticket_list), "teams": len(teams_list)}

os.makedirs("data", exist_ok=True)
with open("data/teams.json",   "w") as f: json.dump(teams_list,  f, separators=(",",":"))
with open("data/tickets.json", "w") as f: json.dump(ticket_list, f, separators=(",",":"))
with open("data/meta.json",    "w") as f: json.dump(meta,        f, separators=(",",":"))
print(f"Wrote {len(teams_list)} teams, {len(ticket_list)} tickets.")
