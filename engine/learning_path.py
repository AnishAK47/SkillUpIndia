RES={"SQL":"SQL querying practice","Python":"Python for data analysis","Power BI":"Power BI dashboards","DAX":"DAX calculations","ETL":"ETL and pipeline fundamentals","Data Pipelines":"Data pipeline design","Data Warehousing":"Dimensional modeling","Azure":"Azure fundamentals","Excel":"Advanced Excel for analytics"}
class LearningPathEngine:
    def build(self,gaps,current):
        cur={str(x).lower() for x in current}; out=[]
        for _,r in gaps.iterrows():
            s=str(r["Market Skill"])
            if s.lower() in cur:continue
            out.append({"Skill":s,"Priority":r["Status"],"Gap Score":float(r["Weighted Gap Score"]),"Why":f"Industry demand is {float(r['Industry Demand Weight'])*100:.0f}% and effective curriculum coverage is {float(r['Effective Coverage'])*100:.0f}%.","Learning Action":RES.get(s,f"Build practical {s} skills")})
        return out
