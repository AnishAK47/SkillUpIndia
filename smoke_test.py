from pathlib import Path
import pandas as pd
from engine.gap_engine import SkillGapEngineV2
from engine.job_ingestor import JobPostingIngestor
from engine.learning_path import LearningPathEngine

base=Path(__file__).parent
d=pd.read_csv(base/"data/skill_demand.csv")
a=pd.read_csv(base/"data/curriculum_skills_pl300.csv")
b=pd.read_csv(base/"data/curriculum_skills_ms_catalog.csv")
m=SkillGapEngineV2().run(d,pd.concat([a,b],ignore_index=True))
assert len(m)>0
jobs=JobPostingIngestor().from_text("We need Python, SQL, Power BI and DAX for data analysis.")
assert jobs[0]["skills"]
path=LearningPathEngine().build(m,["Python"])
assert isinstance(path,list)
print("SkillUpIndia FINAL smoke test: PASS")
print(f"Skills audited: {len(m)}")
print(f"Priority gaps: {int(m.Status.isin(['High','Critical']).sum())}")
