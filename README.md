# SkillUpIndia

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://skillupindia.streamlit.app)

**Live demo:** https://skillupindia.streamlit.app

**Problem statement SIH26134:** Challenges in aligning skill development programs with industry requirements and emerging job-market demands.

SkillUpIndia connects four evidence layers:
**Industry demand → Skills → Curriculum coverage → Learner action**

## Portals and pages

The top navigation groups the pages by who uses them. Anyone can browse and try the tools; an account is needed only to save, and admin pages are hidden from everyone else.

| Portal | Page | Access | What it does |
|---|---|---|---|
| — | **Dashboard** | Everyone | Key metrics (skills tracked, critical and high gaps, curriculum alignment, postings analysed), a demand-vs-coverage chart for the top 10 skills, and action items for every open gap. |
| Government | **Market pulse** | Everyone | The 15 most in-demand skills, the full demand table, and a CSV download. |
| Government | **Data ingestion** | Admin | Paste a job description or upload a job CSV to rebuild the demand baseline. |
| Institutions | **Curriculum audit** | Everyone | The full gap matrix with a minimum-gap filter, the overall alignment score, and a CSV export. |
| Institutions | **Curriculum upload** | Admin | Upload a syllabus PDF and see its gap analysis against current demand. |
| Students | **Student profile** | Everyone; saving needs sign-in | Check demand-weighted readiness and a learning path for a set of skills, and save it as a profile. |
| Students | **Resume to profile** | Everyone; saving needs sign-in | Upload a resume PDF to extract skills and see personalised priorities, then save it as a profile. |
| Students | **Upskill bridge** | Everyone | Pick your current skills and get up to 15 prioritised learning actions, downloadable as CSV. |
| Students | **Progress tracking** | Signed in | Mark each of the top 15 market skills as Not Started, Learning, or Completed for your saved profiles. |
| Account | **Sign in / Account** | Everyone | Sign in or create an account with Google or an email and password, and see your role. |
| Account | **Feedback** | Signed in | Report a skill the parser missed or misread, or a curriculum match or gap score that looks wrong. Pages that show extraction or matching results link straight to it. Admins also see the feedback inbox. |

The app always opens in dark mode over an animated background video, whatever the visitor's system theme.

## Accounts and roles

- **Visitors** can browse every public page, check readiness, and try resume parsing without an account.
- **Members** (anyone who signs in) can save student profiles, track their progress, and send feedback. Members see only their own profiles.
- **Admins** also get Data ingestion, Curriculum upload, the feedback inbox, and every member's profiles.

Sign-in uses Streamlit's built-in `st.login` with Auth0, which provides "Continue with Google" and email-and-password sign-up on one hosted page. Auth0 handles passwords, email verification, and password resets; the app never sees or stores a password.

Admin access is granted to email addresses listed in the app's secrets, and only once that email is verified, so nobody can become an admin by signing up with someone else's address. Profiles are tied to the sign-in provider's account ID rather than the email for the same reason.

## Setup: sign-in and database

Without this setup the app still runs: every page can be browsed, but nothing can be saved. [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) shows every value in one place.

### 1. Auth0 (sign-in)

1. Create a free account at [auth0.com](https://auth0.com), which gives you a tenant domain such as `your-tenant.us.auth0.com`.
2. Go to **Applications → Create Application** and choose **Regular Web Applications**.
3. In the application's **Settings**, set:
   - **Allowed Callback URLs:** `https://skillupindia.streamlit.app/oauth2callback, http://localhost:8501/oauth2callback`
   - **Allowed Logout URLs:** `https://skillupindia.streamlit.app/oauth2callback, http://localhost:8501/oauth2callback` (Streamlit's sign-out returns to the callback address, so it must be listed here too)
4. In the application's **Connections** tab, enable **Username-Password-Authentication** (email and password) and **google-oauth2** (Google). Auth0's built-in Google keys are fine for testing; add your own Google OAuth client in **Authentication → Social** before real use.
5. Copy the **Domain**, **Client ID**, and **Client Secret**.

### 2. Supabase (database)

1. Create a free project at [supabase.com](https://supabase.com).
2. Open **SQL Editor**, paste the contents of [`supabase/schema.sql`](supabase/schema.sql), and run it.
3. In **Project Settings → API Keys**, copy the project URL and a **secret** key (`sb_secret_…`, or the legacy `service_role` key). This key bypasses row-level security, so keep it only in secrets.

### 3. Streamlit secrets

In Streamlit Community Cloud, open the app's **Settings → Secrets** and paste the following with your values. For local runs, save it as `.streamlit/secrets.toml` (git-ignored) with `redirect_uri` set to `http://localhost:8501/oauth2callback`.

```toml
[auth]
redirect_uri = "https://skillupindia.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-string"
client_id = "your-auth0-client-id"
client_secret = "your-auth0-client-secret"
server_metadata_url = "https://YOUR-TENANT.us.auth0.com/.well-known/openid-configuration"

[access]
admins = ["you@example.com"]

[supabase]
url = "https://YOUR-PROJECT.supabase.co"
service_role_key = "your-secret-key"
```

Generate `cookie_secret` with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### 4. Optional: feedback as GitHub issues

To also open each feedback report as an issue on this repo, create a [fine-grained GitHub token](https://github.com/settings/personal-access-tokens/new) limited to this repository with **Issues: Read and write**, and add it to the secrets:

```toml
[github]
token = "your-token"
repo = "AnishAK47/SkillUpIndia"
```

The form then warns users that reports are public. The reporter's email is stored only in the database, never in the issue.

## 5-minute demo

Run this on the live site. Numbers refer to the bundled demo data. Steps 5 and 6 need an account, and step 7 needs an admin account.

1. **Dashboard:** walk through the four metrics. In the chart, Data Analysis and Data Quality have demand but no coverage bar, and the same skills top the action items.
2. **Government → Market pulse:** SQL is in 70% of postings, and Power BI and Python in 60%.
3. **Institutions → Curriculum audit:** raise *Minimum gap score* to 0.25 and only the critical gap remains. Hover a column header to explain how each score is calculated.
4. **Students → Upskill bridge:** select a few skills, such as SQL and Excel, to see the prioritised learning actions.
5. **Students → Resume to profile:** upload any text-based resume PDF, review the extracted skills and priorities, then sign in and save it as a profile.
6. **Students → Progress tracking:** choose that profile and mark a skill as Learning or Completed.
7. **Government → Data ingestion (admin, do this last):** paste a job description and click *Extract & ingest*, or upload `demo_data/sample_job_postings.csv` under *CSV dataset upload*. The dashboard metrics now reflect those postings. Ingestion replaces the demand baseline for your session, and reloading the page restores the demo data.

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

Check the core engine, and the access rules for visitors, members, and admins:

```bash
python smoke_test.py
python -m pytest tests
```

## Data and inputs

- `data/skill_demand.csv`: demo demand data built from 10 job postings.
- `data/curriculum_skills_pl300.csv` and `data/curriculum_skills_ms_catalog.csv`: curriculum topics with teaching-depth weights, from the PL-300 syllabus and Microsoft catalog courses.
- `demo_data/sample_job_postings.csv`: 10 fictional postings, ready to upload in Data ingestion.
- **Job CSV (Data ingestion):** any columns work. Skills are detected from all the text in each row. `job_id`, `job_title` (or `title`), `company`, and `location` are used when present.
- **Resume and curriculum PDFs:** text-based PDFs only. Scanned images contain no extractable text.

## Architecture

Job data → skill extraction → demand matrix → curriculum parsing → skill matching → gap scoring → recommendations → student profile → learning path → progress.

- `app.py`: the Streamlit app, with pages, navigation, sign-in, and styling.
- `engine/`: ingestion, skill extraction, gap scoring, learning paths, PDF parsing, and storage (Supabase when configured, otherwise a local SQLite file).
- `supabase/schema.sql`: the database tables, with row-level security enabled.
- `tests/`: access-rule tests for visitors, members, and admins.
- `.streamlit/config.toml`: the dark theme.
- `assets/`: the background video. `scripts/make_bg_loop.py` regenerates the seamless loop from the source clip.

## Prototype disclosure

- The demand data is a small demonstration dataset (10 postings), not live job-board data.
- Skill extraction matches keywords against a fixed vocabulary of about 40 skills and their aliases. It detects that a skill is mentioned, not proficiency or experience.
- Curriculum matching uses a curated skill-to-topic mapping plus name overlap, not semantic similarity.
- Data ingestion changes the demand baseline only for the current browser session.
- Saved profiles, progress, and feedback persist in Supabase when it's configured. Without it they're stored in a local SQLite file, which on the hosted demo resets whenever the app restarts or redeploys.
- Readiness and gap scores are decision-support metrics, not hiring probabilities.

## Production roadmap

Live job-board and API connectors, larger district and sector datasets, transformer-based skill extraction with domain guardrails, a hosted API layer, monitoring, and scheduled data refresh.
