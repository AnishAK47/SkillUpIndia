import pandas as pd
from engine.skill_utils import extract_skills,normalize_skill,build_demand
class JobPostingIngestor:
    def from_csv(self,f):
        df=pd.read_csv(f); jobs=[]
        for i,row in df.iterrows():
            text=" ".join(map(str,row.to_dict().values()))
            jobs.append({"job_id":str(row.get("job_id",f"JOB{i+1:03d}")),"title":str(row.get("job_title",row.get("title","Unknown Role"))),"company":str(row.get("company","")),"location":str(row.get("location","")),"description":text,"skills":extract_skills(text)})
        return jobs
    def from_text(self,text,title="Pasted Job",company=""):
        return [{"job_id":"PASTE001","title":title,"company":company,"location":"","description":text,"skills":extract_skills(text)}]
    def normalize_jobs(self,jobs):
        for j in jobs:j["skills"]=sorted(set(normalize_skill(s) for s in j["skills"]))
        return jobs
    def demand(self,jobs):return build_demand(self.normalize_jobs(jobs))
