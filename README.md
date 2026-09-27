# SkillUpIndia

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://skillupindia.streamlit.app)

**Live demo:** https://skillupindia.streamlit.app

**Problem statement SIH26134:** Challenges in aligning skill development programs with industry requirements and emerging job-market demands.

SkillUpIndia connects four evidence layers:
**Industry demand → Skills → Curriculum coverage → Learner action**

## Portals and pages

The top navigation groups the pages by who uses them.

| Portal | Page | What it does |
|---|---|---|
| — | **Dashboard** | Key metrics (skills tracked, critical and high gaps, curriculum alignment, postings analysed), a demand-vs-coverage chart for the top 10 skills, and action items for every open gap. |
| Government | **Market pulse** | The 15 most in-demand skills, the full demand table, and a CSV download. |
| Government | **Data ingestion** | Paste a job description or upload a job CSV to rebuild the demand baseline. |
| Institutions | **Curriculum audit** | The full gap matrix with a minimum-gap filter, the overall alignment score, and a CSV export. |
| Institutions | **Curriculum upload** | Upload a syllabus PDF and see its gap analysis against current demand. |
| Students | **Student profile** | Save a profile with a target role and skills, then see demand-weighted readiness and a learning path. |
| Students | **Resume to profile** | Upload a resume PDF to extract skills, see personalised priorities, and save it as a profile. |
| Students | **Upskill bridge** | Pick your current skills and get up to 15 prioritised learning actions, downloadable as CSV. |
| Students | **Progress tracking** | Mark each of the top 15 market skills as Not Started, Learning, or Completed for a saved profile. |

Switch to dark mode (⋮ menu → Settings → Theme) to see the animated background.

## 5-minute demo

Run this on the live site. Numbers refer to the bundled demo data.

1. **Dashboard:** walk through the four metrics. In the chart, Data Analysis and Data Quality have demand but no coverage bar, and the same skills top the action items.
2. **Government → Market pulse:** SQL is in 70% of postings, and Power BI and Python in 60%.
3. **Institutions → Curriculum audit:** raise *Minimum gap score* to 0.25 and only the critical gap remains. Hover a column header to explain how each score is calculated.
4. **Students → Upskill bridge:** select a few skills, such as SQL and Excel, to see the prioritised learning actions.
5. **Students → Resume to profile:** upload any text-based resume PDF, review the extracted skills and priorities, then save it as a profile.
6. **Students → Progress tracking:** choose that profile and mark a skill as Learning or Completed.
7. **Government → Data ingestion (do this last):** paste a job description and click *Extract & ingest*. The dashboard metrics now reflect that posting. Ingestion replaces the demand baseline for your session, and reloading the page restores the demo data.

## How the scores are calculated

- **Demand:** the share of analysed job postings that mention a skill.
- **Match:** 1 for a curated exact mapping to a curriculum topic, 0.75 for a partial name match, and 0 otherwise. Matches below 0.6 count as no match.
- **Coverage:** match × the depth at which the matched topic is taught.
- **Gap score:** demand × (1 − coverage). Status is Critical at 0.40 or above, High at 0.25, Moderate at 0.12, and Low below that.
- **Curriculum alignment:** 100% minus the average gap score.
- **Demand-weighted readiness:** the share of total demand covered by a student's skills.

## Run locally

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py
```

On macOS you can also run `./launch_demo.sh`, which does both steps.

Check the core engine without starting the app:

```bash
python smoke_test.py
```

## Data and inputs

- `data/skill_demand.csv`: demo demand data built from 10 job postings.
- `data/curriculum_skills_pl300.csv` and `data/curriculum_skills_ms_catalog.csv`: curriculum topics with teaching-depth weights, from the PL-300 syllabus and Microsoft catalog courses.
- **Job CSV (Data ingestion):** any columns work. Skills are detected from all the text in each row. `job_id`, `job_title` (or `title`), `company`, and `location` are used when present.
- **Resume and curriculum PDFs:** text-based PDFs only. Scanned images contain no extractable text.

## Architecture

Job data → skill extraction → demand matrix → curriculum parsing → skill matching → gap scoring → recommendations → student profile → learning path → progress.

- `app.py`: the Streamlit app, with pages, navigation, and styling.
- `engine/`: ingestion, skill extraction, gap scoring, learning paths, PDF parsing, and SQLite storage.
- `.streamlit/config.toml`: the light and dark themes.
- `assets/`: the background video. `scripts/make_bg_loop.py` regenerates the seamless loop from the source clip.

## Prototype disclosure

- The demand data is a small demonstration dataset (10 postings), not live job-board data.
- Skill extraction matches keywords against a fixed vocabulary of about 40 skills and their aliases. It detects that a skill is mentioned, not proficiency or experience.
- Curriculum matching uses a curated skill-to-topic mapping plus name overlap, not semantic similarity.
- Data ingestion changes the demand baseline only for the current browser session.
- On the hosted demo, saved profiles and progress are stored in a local SQLite file and reset whenever the app restarts or redeploys.
- Readiness and gap scores are decision-support metrics, not hiring probabilities.

## Production roadmap

Live job-board and API connectors, larger district and sector datasets, transformer-based skill extraction with domain guardrails, a persistent hosted database and API layer, authentication, monitoring, and scheduled data refresh.
