import math, random, re, time
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup

MANIFEST = "manifest_2024_geometry_clean.csv"
OUT = "netkeiba_200m_laps_2024_clean.csv"
FAIL = "failed_urls_2024_geometry.csv"
LOCKED_HOLDOUT = "202301020411"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
})

def parse_sectionals(html, distance):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    mt = re.search(r"SECTIONAL TIMES(.*?)(?:MENU|RACING MENU|$)", text, flags=re.S|re.I)
    if not mt:
        return None
    block = mt.group(1)

    vals = []
    for token in re.findall(r"(?<![:\d])(\d{1,2}\.\d)(?!\d)", block):
        v = float(token)
        if 8.0 <= v <= 20.0:
            vals.append(v)

    # 1800m -> 9 splits, 2000m -> 10, 2500m -> 13 (first segment may be 100m).
    expected = int(math.ceil(float(distance) / 200.0))
    if len(vals) < expected:
        return None

    cand_first = vals[:expected]
    cand_last = vals[-expected:]
    def score(seq):
        plausible = sum(9.0 <= x <= 16.5 for x in seq)
        jumps = sum(abs(b-a) > 3.2 for a,b in zip(seq, seq[1:]))
        return plausible - 2*jumps
    seq = cand_last if score(cand_last) > score(cand_first) else cand_first

    if len(seq) != expected:
        return None
    return seq

df = pd.read_csv(MANIFEST, dtype={"past_race_id_str":str})
df = df[df["use_flag"].eq("YES")].copy()
rows, fails = [], []

for _, r in df.iterrows():
    rid = str(r["past_race_id_str"])
    if rid == LOCKED_HOLDOUT:
        continue
    url = str(r["netkeiba_en_url"])
    ok = False
    err = ""
    for attempt in range(6):
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                laps = parse_sectionals(res.text, r["distance"])
                if laps:
                    rec = {
                        "race_id": rid,
                        "source_url": url,
                        "distance": r["distance"],
                        "venue": r["past_venue"],
                        "n_laps": len(laps),
                    }
                    for j, v in enumerate(laps, 1):
                        rec[f"lap_{j}"] = v
                    rows.append(rec)
                    ok = True
                    break
                err = "parse_failed"
            else:
                err = f"http_{res.status_code}"
        except Exception as e:
            err = repr(e)
        time.sleep(2.0 + attempt*2.0 + random.random())
    if not ok:
        fails.append({"race_id":rid, "url":url, "error":err})
    time.sleep(1.0 + random.random()*0.7)

pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
pd.DataFrame(fails).to_csv(FAIL, index=False, encoding="utf-8-sig")
print("success", len(rows), "failed", len(fails))
