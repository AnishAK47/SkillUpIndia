import pandas as pd
from engine.skill_utils import normalize_skill
MAP={"SQL":["SQL Database Administration and Querying"],"Database Querying":["SQL Database Administration and Querying"],"Python":["Python Scripting and Data Notebooks"],"Power BI":["Data Modeling in Power BI"],"DAX":["DAX Expressions and Calculations"],"Data Modelling":["Data Modeling in Power BI","Data Warehousing and Dimensional Modeling"],"ETL":["Enterprise ETL and Data Pipelines"],"Data Pipelines":["Enterprise ETL and Data Pipelines"],"Data Warehousing":["Data Warehousing and Dimensional Modeling"],"Excel":["Basic Excel Integration"],"Azure":["Azure Cloud Architecture and Core Compute"],"GCP":["Azure Cloud Architecture and Core Compute"]}
class SkillGapEngineV2:
    def __init__(self,match_threshold=.6):self.match_threshold=match_threshold
    def run(self,demand,curriculum):
        out=[]
        for _,d in demand.iterrows():
            skill=normalize_skill(d.skill_normalized); best=(0,None,None)
            for i,r in curriculum.iterrows():
                n=str(r.Skill); score=1 if n.lower() in [x.lower() for x in MAP.get(skill,[])] or n.lower()==skill.lower() else .75 if skill.lower() in n.lower() or n.lower() in skill.lower() else 0
                if score>best[0]:best=(score,i,r)
            sim,i,r=best
            if sim>=self.match_threshold:
                curr=str(r.Skill); depth=float(r.DepthWeight); source=str(r.get("Course",r.get("source","Curriculum")))
            else:curr="None";depth=0;source="N/A"
            cov=sim*depth; gap=max(0,float(d.demand_percentage)/100*(1-cov))
            status="Critical" if gap>=.4 else "High" if gap>=.25 else "Moderate" if gap>=.12 else "Low"
            out.append({"Market Skill":skill,"Industry Demand Weight":round(float(d.demand_percentage)/100,2),"Best Curriculum Match":curr,"Semantic Similarity":round(sim,2),"Curriculum Depth Weight":round(depth,2),"Effective Coverage":round(cov,2),"Source Framework":source,"Weighted Gap Score":round(gap,2),"Status":status})
        return pd.DataFrame(out).sort_values("Weighted Gap Score",ascending=False).reset_index(drop=True)
