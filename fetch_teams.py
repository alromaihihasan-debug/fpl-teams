"""FPL team bridge v2: on-demand + scheduled.
- Dispatched with a TEAM_ID input: fetches that one team (any ID) and auto-registers it
  in teams.txt for future scheduled refreshes.
- Scheduled run (no input): refreshes every registered team.
Saves: entry.json, history.json, transfers.json, picks_gw{N}.json per team."""
import json, os, urllib.request, pathlib, time

BASE = "https://fantasy.premierleague.com/api"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))

boot = get(f"{BASE}/bootstrap-static/")
current = next((e["id"] for e in boot["events"] if e["is_current"]), None) or \
          max((e["id"] for e in boot["events"] if e["finished"]), default=1)

reg = pathlib.Path("teams.txt")
ids = [l.strip() for l in reg.read_text().splitlines() if l.strip().isdigit()] if reg.exists() else []
one = os.environ.get("TEAM_ID", "").strip()
todo = [one] if one.isdigit() else ids
if one.isdigit() and one not in ids:
    ids.append(one); reg.write_text("\n".join(ids) + "\n")   # auto-register new ID

for tid in todo:
    d = pathlib.Path(f"teams/{tid}"); d.mkdir(parents=True, exist_ok=True)
    try:
        (d/"entry.json").write_text(json.dumps(get(f"{BASE}/entry/{tid}/"), indent=1))
        (d/"history.json").write_text(json.dumps(get(f"{BASE}/entry/{tid}/history/"), indent=1))
        (d/"transfers.json").write_text(json.dumps(get(f"{BASE}/entry/{tid}/transfers/"), indent=1))
        for gw in range(max(1, current-1), current+1):
            try:
                (d/f"picks_gw{gw}.json").write_text(json.dumps(get(f"{BASE}/entry/{tid}/event/{gw}/picks/"), indent=1))
            except Exception as e:
                print(f"team {tid} gw {gw}: {e}")
    except Exception as e:
        print(f"team {tid}: FAILED ({e})")
    time.sleep(1)
pathlib.Path("teams").mkdir(exist_ok=True)
(pathlib.Path("teams")/"meta.json").write_text(json.dumps({"current_gw": current, "teams": ids, "last": todo}))
print(f"synced {todo} at GW{current}")
