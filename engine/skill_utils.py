import re
import pandas as pd
ALIASES={"powerbi":"Power BI","power-bi":"Power BI","sql server":"SQL","mysql":"SQL","postgresql":"SQL","python3":"Python","git":"Git/GitHub","github":"Git/GitHub","data modeling":"Data Modelling","data modelling":"Data Modelling","google cloud":"GCP","azure cloud":"Azure"}
SKILLS=["Python","SQL","Power BI","DAX","Excel","R","C#",".NET","GCP","Azure","SSAS","ETL","Data Analysis","Data Analytics","Data Cleaning","Data Quality","Data Validation","Database Querying","Data Modelling","Data Pipelines","Data Warehousing","Data Visualization","Dashboarding","Data Interpretation","Data Collection","Reporting","Statistics","Communication","Git/GitHub","Version Control","REST APIs","Looker","Marketing Analytics","Machine Learning","Generative AI","Power Query","Data Security","RLS"]
def normalize_skill(x):
    s=re.sub(r"\s+"," ",str(x or "").strip()); k=s.lower()
    if k in ALIASES:return ALIASES[k]
    for a,c in ALIASES.items():
        if a in k:return c
    for v in SKILLS:
        if k==v.lower():return v
    return s
def extract_skills(text):
    low=str(text or "").lower(); out=[]
    for s in SKILLS:
        if re.search(r"(?<!\w)"+re.escape(s.lower())+r"(?!\w)",low):out.append(s)
    for a,c in ALIASES.items():
        if re.search(r"(?<!\w)"+re.escape(a)+r"(?!\w)",low):out.append(c)
    return sorted(set(out))
def build_demand(jobs):
    rows=[]
    for j in jobs:
        for s in set(normalize_skill(x) for x in j.get("skills",[])):
            rows.append((j.get("job_id",""),s))
    if not rows:return pd.DataFrame(columns=["skill_normalized","job_count","demand_percentage"])
    df=pd.DataFrame(rows,columns=["job_id","skill_normalized"]).drop_duplicates()
    n=max(1,df.job_id.nunique())
    o=df.groupby("skill_normalized").job_id.nunique().reset_index(name="job_count")
    o["demand_percentage"]=(o.job_count/n*100).round(1)
    return o.sort_values("demand_percentage",ascending=False).reset_index(drop=True)
