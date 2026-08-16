import re, time, random
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup

RETRY_MANIFEST="retry7_manifest.csv"
MASTER="netkeiba_200m_laps_2022_validation.csv"
FAIL="failed_urls.csv"

s=requests.Session()
s.headers.update({
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept-Language":"en-US,en;q=0.9,ja;q=0.7",
})

def parse_sectionals(html):
    soup=BeautifulSoup(html,"html.parser")
    txt=soup.get_text(" ",strip=True)
    # Netkeiba English page normally exposes "SECTIONAL TIMES".
    # Extract time-like decimals after the label and validate plausible 200m splits.
    m=re.search(r"SECTIONAL\s+TIMES?(.*?)(?:HORSE|PAYOFF|CORNER|RESULT|$)",txt,re.I)
    segment=m.group(1) if m else txt
    vals=[float(x) for x in re.findall(r"(?<!\d)(\d{1,2}\.\d)(?!\d)",segment)]
    # plausible 200m splits are usually 9.0–16.5 sec
    vals=[x for x in vals if 9.0 <= x <= 16.5]
    # Find a plausible contiguous lap sequence, prefer 7–18 laps.
    if len(vals) < 7:
        return None
    # The first plausible block is generally the sectional list on this page.
    return vals[:18]

m=pd.read_csv(RETRY_MANIFEST,dtype={"race_id":str})
rows=[]; fails=[]
for _,r in m.iterrows():
    rid=str(r["race_id"]); url=str(r["url"])
    ok=False
    for attempt in range(6):
        try:
            res=s.get(url,timeout=30)
            if res.status_code==200:
                laps=parse_sectionals(res.text)
                if laps and len(laps)>=7:
                    rec={"race_id":rid,"source_url":url,"n_laps":len(laps)}
                    for i,x in enumerate(laps,1):
                        rec[f"lap_{i}"]=x
                    rows.append(rec); ok=True; break
        except Exception:
            pass
        time.sleep(3 + attempt*3 + random.random()*2)
    if not ok:
        fails.append({"race_id":rid,"url":url})
    time.sleep(1.5+random.random())

new=pd.DataFrame(rows)
if Path(MASTER).exists():
    old=pd.read_csv(MASTER,dtype={"race_id":str})
    if len(new):
        allcols=sorted(set(old.columns)|set(new.columns),
                       key=lambda x:(0 if x in ["race_id","source_url","n_laps"] else 1,x))
        old=old.reindex(columns=allcols)
        new=new.reindex(columns=allcols)
        merged=pd.concat([old,new],ignore_index=True)
        merged=merged.drop_duplicates("race_id",keep="last")
    else:
        merged=old
else:
    merged=new

merged.to_csv(MASTER,index=False,encoding="utf-8-sig")
pd.DataFrame(fails,columns=["race_id","url"]).to_csv(FAIL,index=False,encoding="utf-8-sig")

print("retry success:",len(rows))
print("retry failed:",len(fails))
print("master races:",merged["race_id"].nunique() if len(merged) else 0)
if fails:
    print("remaining:",",".join(x["race_id"] for x in fails))
