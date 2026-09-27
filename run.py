from pathlib import Path
import pandas as pd
from engine.gap_engine import SkillGapEngineV2
b=Path(__file__).parent;d=pd.read_csv(b/"data/skill_demand.csv");a=pd.read_csv(b/"data/curriculum_skills_pl300.csv");x=pd.read_csv(b/"data/curriculum_skills_ms_catalog.csv");m=SkillGapEngineV2().run(d,pd.concat([a,x],ignore_index=True));(b/"output").mkdir(exist_ok=True);m.to_csv(b/"output/skill_gap_matrix.csv",index=False);print(m.to_string(index=False))
