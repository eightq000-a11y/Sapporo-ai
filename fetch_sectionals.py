import csv, re, time, random, sys, os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pandas as pd

HOLDOUT="202301020411"
MANIFEST="manifest_2022_validation.csv"
OUT="netkeiba_200m_laps_2022_validation.csv"
FAIL="failed_urls.csv"

session=requests.Session()
session.headers.update({
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept-Language":"en-US,en;q=0.9,ja;q=0.8",
})

def parse_sectionals(html):
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text("\n", strip=True)
    m=re.search(r"SECTIONAL TIMES(.*?)(?:MENU|RACING MENU|$)", text, flags=re.S|re.I)
    if not m:
        return None
    block=m.group(1)
    # Prefer the lower-row sectional numbers, which are usually 8.0–20.0 sec.
    vals=[]
    for token in re.findall(r"(?<![:\d])(\d{1,2}\.\d)(?!\d)", block):
        v=float(token)
        if 8.0 <= v <= 20.0:
            vals.append(v)
    # Sectional block may include each first cumulative time once; infer expected count from distance labels.
    dist_labels=[int(x) for x in re.findall(r"\b(\d{3,4})m\b", block)]
    expected=max(dist_labels)//200 if dist_labels else None
    if expected and len(vals)>=expected:
        # In the rendered block, sectional values occur in order; keep last expected plausible values
        # only if that produces a realistic sequence. Otherwise use first expected.
        cand1=vals[:expected]
        cand2=vals[-expected:]
        def plaus(seq): return sum(1 for x in seq if 9.0 <= x <= 15.5)
        vals=cand2 if plaus(cand2)>plaus(cand1) else cand1
    if expected and len(vals)!=expected:
        return None
    return vals

df=pd.read_csv(MANIFEST, dtype={"past_race_id_str":str})
rows=[]; fails=[]
for i,r in df.iterrows():
    rid=str(r["past_race_id_str"])
    if rid==HOLDOUT:
        continue
    url=str(r["netkeiba_en_url"])
    ok=False
    for attempt in range(3):
        try:
            res=session.get(url,timeout=25)
            if res.status_code==200:
                laps=parse_sectionals(res.text)
                if laps:
                    rec={"race_id":rid, "source_url":url, "n_laps":len(laps)}
                    for j,v in enumerate(laps,1):
                        rec[f"lap_{j}"]=v
                    rows.append(rec); ok=True; break
        except Exception as e:
            err=repr(e)
        time.sleep(2.0+attempt*2+random.random())
    if not ok:
        fails.append({"race_id":rid,"url":url})
    time.sleep(1.0+random.random()*0.6)

pd.DataFrame(rows).to_csv(OUT,index=False,encoding="utf-8-sig")
pd.DataFrame(fails).to_csv(FAIL,index=False,encoding="utf-8-sig")
print("success",len(rows),"failed",len(fails))
