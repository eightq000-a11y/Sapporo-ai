import re, time, random
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup

MANIFEST="pedigree_manifest_train_validation.csv"
OUT="pedigree_5gen_train_validation.csv"
FAIL="pedigree_failed.csv"

s=requests.Session()
s.headers.update({
 "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
 "Accept-Language":"ja,en-US;q=0.8,en;q=0.7",
})

def clean(x):
    x=re.sub(r"\s+"," ",x or "").strip()
    x=re.sub(r"\s*\([^)]*\)\s*$","",x).strip()
    x=re.sub(r"\s+\d{4}.*$","",x).strip()
    return x

def parse_pedigree(html):
    soup=BeautifulSoup(html,"html.parser")
    # netkeiba pedigree pages expose the 5-generation pedigree as a table.
    tables=soup.find_all("table")
    ped=None
    for t in tables:
        txt=t.get_text(" ",strip=True)
        if len(t.find_all("td"))>=20 and ("血統" in txt or len(txt)>200):
            ped=t
            break
    if ped is None:
        return None
    # Capture horse names in DOM order. Repeated rowspan cells are intentionally
    # retained only once by BeautifulSoup, matching the pedigree tree entries.
    names=[]
    for td in ped.find_all("td"):
        a=td.find("a")
        txt=clean(a.get_text(" ",strip=True) if a else td.get_text(" ",strip=True))
        if not txt or txt in {"血統","産駒"}:
            continue
        # discard percentages/cross notes/noise
        if re.fullmatch(r"[\d.%xX ]+",txt):
            continue
        names.append(txt)
    # first entries should be sire-side followed by dam-side branches.
    # Store raw ordered list; downstream parser will reconstruct side/generation.
    return names

m=pd.read_csv(MANIFEST,dtype={"horse_id":str})
rows=[]; fails=[]
for i,r in m.iterrows():
    hid=str(r["horse_id"]); url=str(r["pedigree_url"])
    ok=False
    for attempt in range(3):
        try:
            res=s.get(url,timeout=25)
            if res.status_code==200:
                names=parse_pedigree(res.text)
                if names and len(names)>=20:
                    rec={"horse_id":hid,"horse_name":r["horse_name"],"source_url":url,"pedigree_entry_count":len(names)}
                    for j,n in enumerate(names,1):
                        rec[f"ped_{j:02d}"]=n
                    rows.append(rec); ok=True; break
        except Exception:
            pass
        time.sleep(2+attempt*2+random.random())
    if not ok:
        fails.append({"horse_id":hid,"horse_name":r["horse_name"],"url":url})
    time.sleep(.9+random.random()*.5)
    if (i+1)%100==0:
        pd.DataFrame(rows).to_csv(OUT,index=False,encoding="utf-8-sig")
        pd.DataFrame(fails).to_csv(FAIL,index=False,encoding="utf-8-sig")
        print(i+1,"success",len(rows),"failed",len(fails),flush=True)

pd.DataFrame(rows).to_csv(OUT,index=False,encoding="utf-8-sig")
pd.DataFrame(fails).to_csv(FAIL,index=False,encoding="utf-8-sig")
print("DONE success",len(rows),"failed",len(fails))
