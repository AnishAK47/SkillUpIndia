# SkillUpIndia — FINAL SIH DEMO

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://skillupindia.streamlit.app)

**Live demo:** https://skillupindia.streamlit.app

**Problem:** SIH26134 — Challenges in aligning skill development programs with industry requirements and emerging job-market demands.

## Final product
SkillUpIndia connects four evidence layers:
**Industry demand → Skills → Curriculum coverage → Learner action**

## Demo modules
- Dashboard — executive overview
- Market Pulse — role-focused industry skill demand
- Curriculum Audit — curriculum coverage and weighted gaps
- Upskill Bridge — prioritized learning actions
- Student Profile — demand-weighted readiness
- Resume → Profile — explicit skill extraction and personalized priorities
- Progress Tracking — persistent learner progress
- Curriculum Upload — PDF curriculum audit
- Data Ingestion — job CSV / pasted JD ingestion
- SIH Report — presentation-ready summary

## Recommended 5-minute demo
1. Open Dashboard and select **Data Analyst**.
2. Show Market Pulse: SQL / Power BI / Python demand.
3. Open Curriculum Audit: show where demand is under-covered.
4. Open Upskill Bridge: show the resulting learning actions.
5. Upload a sample resume in Resume → Profile.
6. Show extracted skills and personalized priorities.
7. Save the profile and open Progress Tracking.
8. Finish on SIH Report to explain impact and prototype boundaries.

## One-command launch on macOS
From Documents:
```bash
cd ~/Documents/SkillUpIndia_FINAL && python3 -m pip install -r requirements.txt && python3 -m streamlit run app.py
```

## Important prototype disclosure
The current job dataset is a demonstration dataset. Role filters are configured prototype mappings. Resume parsing detects explicit skill mentions and does not establish proficiency or validate experience. Readiness and gap scores are decision-support metrics, not hiring probabilities.

## Architecture
Job data → skill extraction → demand matrix → curriculum parsing → skill matching → gap scoring → recommendations → student profile → learning path → progress.

## Production roadmap
Live job-board/API connectors, larger district/sector datasets, stronger transformer-based extraction with domain guardrails, hardened database/API layer, authentication, deployment, monitoring and scheduled data refresh.
