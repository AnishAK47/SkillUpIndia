import pandas as pd
import streamlit as st
from pathlib import Path
import plotly.express as px
from engine.job_ingestor import JobPostingIngestor
from engine.resume_parser import ResumeParser
from engine.gap_engine import SkillGapEngineV2
from engine.learning_path import LearningPathEngine
from engine.data_store import SkillUpStore
from engine.curriculum_parser import CurriculumPDFParser

# 1. Page configuration
# Colors, fonts, radius, and button styling live in .streamlit/config.toml so
# they stay consistent across every native widget and survive Streamlit upgrades.
st.set_page_config(page_title="SkillUpIndia", page_icon=":material/target:", layout="wide", initial_sidebar_state="expanded")

# A slow-drifting gradient-mesh background, tinted to match whichever theme
# (light/dark/system) is actually active right now. Combined with the hero
# banner, metric-card hover polish, and scroll-in motion into ONE st.html
# call below: Streamlit only renders the first style-only st.html element
# per rerun, so a second standalone <style>-only call gets silently dropped.
# Dark mode itself is native: users switch it from the app's Settings menu
# (top-right kebab menu -> Settings -> Theme), no custom toggle needed.
_theme_type = st.context.theme.type
if _theme_type == "dark":
    _c1, _c2, _c3 = "rgba(129, 140, 248, 0.22)", "rgba(196, 181, 253, 0.16)", "rgba(34, 211, 238, 0.10)"
else:
    _c1, _c2, _c3 = "rgba(79, 70, 229, 0.16)", "rgba(124, 58, 237, 0.12)", "rgba(8, 145, 178, 0.08)"

_mesh_css = """
[data-testid="stApp"] {
    background-image:
        radial-gradient(circle, __C1__, transparent 60%),
        radial-gradient(circle, __C2__, transparent 60%),
        radial-gradient(circle, __C3__, transparent 65%);
    background-repeat: no-repeat;
    background-size: 55% 55%, 50% 50%, 60% 60%;
    background-position: 10% 15%, 85% 10%, 50% 95%;
    animation: skillup-mesh-drift 28s ease-in-out infinite alternate;
}
@keyframes skillup-mesh-drift {
    0%   { background-position: 10% 15%, 85% 10%, 50% 95%; }
    50%  { background-position: 22% 28%, 72% 24%, 62% 82%; }
    100% { background-position: 6% 10%, 92% 6%, 38% 98%; }
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stApp"] { animation: none; }
}
""".replace("__C1__", _c1).replace("__C2__", _c2).replace("__C3__", _c3)

st.html("<style>" + _mesh_css + """
.hero {
    padding: 3rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #1e1b4b 0%, #4c1d95 55%, #312e81 100%);
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 20px 40px -12px rgba(76, 29, 149, 0.35);
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 80% 15%, rgba(129, 140, 248, 0.35), transparent 55%);
    pointer-events: none;
    z-index: 1;
}
.hero h1 {
    font-size: 2.75rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    color: #f5f3ff;
    position: relative;
    z-index: 2;
}
.hero p {
    font-size: 1.15rem;
    color: #c7d2fe;
    margin: 0;
    position: relative;
    z-index: 2;
}

/* CSS stand-in for the neural-node / fiber-optic hero video: glowing nodes in
   cyan/saffron/magenta with light pulses traveling along thin beam lines.
   Pure CSS so it costs nothing and needs no GPU/video pipeline; swap the
   .hero markup for a real video element later if/when the generated clip is ready. */
.hero-fx {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}
.hero-fx .node {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: skillup-node-pulse 3.6s ease-in-out infinite;
}
.hero-fx .n1 { top: 18%; left: 10%; background: #00c2ff; box-shadow: 0 0 18px 4px rgba(0, 194, 255, 0.7); animation-delay: 0s; }
.hero-fx .n2 { top: 66%; left: 20%; background: #ea580c; box-shadow: 0 0 18px 4px rgba(234, 88, 12, 0.65); animation-delay: 0.6s; }
.hero-fx .n3 { top: 32%; left: 46%; background: #e879f9; box-shadow: 0 0 16px 4px rgba(232, 121, 249, 0.55); animation-delay: 1.2s; }
.hero-fx .n4 { top: 76%; left: 60%; background: #00c2ff; box-shadow: 0 0 18px 4px rgba(0, 194, 255, 0.6); animation-delay: 1.8s; }
.hero-fx .n5 { top: 20%; left: 80%; background: #ea580c; box-shadow: 0 0 16px 4px rgba(234, 88, 12, 0.55); animation-delay: 2.4s; }
.hero-fx .beam {
    position: absolute;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 194, 255, 0.9), transparent);
    background-size: 220% 100%;
    animation: skillup-beam-travel 4.5s linear infinite;
}
.hero-fx .b1 { top: 22%; left: 8%; width: 42%; transform: rotate(7deg); animation-delay: 0s; }
.hero-fx .b2 { top: 60%; left: 18%; width: 46%; transform: rotate(-6deg); background: linear-gradient(90deg, transparent, rgba(234, 88, 12, 0.85), transparent); background-size: 220% 100%; animation-delay: 1.5s; }
.hero-fx .b3 { top: 42%; left: 44%; width: 38%; transform: rotate(4deg); background: linear-gradient(90deg, transparent, rgba(232, 121, 249, 0.8), transparent); background-size: 220% 100%; animation-delay: 3s; }
@keyframes skillup-node-pulse {
    0%, 100% { opacity: 0.35; transform: scale(0.85); }
    50% { opacity: 1; transform: scale(1.15); }
}
@keyframes skillup-beam-travel {
    0% { background-position: 220% 0; opacity: 0; }
    12% { opacity: 1; }
    88% { opacity: 1; }
    100% { background-position: -220% 0; opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
    .hero-fx .node, .hero-fx .beam { animation: none; opacity: 0.5; }
}
[data-testid="stMetric"] {
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-top-color 0.2s ease;
    border-top: 3px solid transparent !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 25px -10px rgba(124, 58, 237, 0.35);
    border-top-color: #7c3aed !important;
}

/* Scroll-in reveal: pure progressive enhancement. Browsers without
   animation-timeline support (Firefox/Safari as of writing) simply skip the
   @supports block and render everything normally, so nothing ever breaks. */
@supports (animation-timeline: view()) {
    .hero,
    [data-testid="stMetric"],
    [data-testid="stDataFrame"],
    [data-testid="stPlotlyChart"],
    [data-testid="stExpander"] {
        animation: skillup-fade-in linear both;
        animation-timeline: view();
        animation-range: entry 0% cover 35%;
    }
}
@keyframes skillup-fade-in {
    from { opacity: 0; transform: translateY(28px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""")

# 2. Setup & data loading
BASE = Path(__file__).parent
DATA = BASE / "data"
store = SkillUpStore(str(BASE / "skillupindia.db"))
ROLE_OPTIONS = ["Data Analyst", "Business Analyst", "Data Engineer", "Power BI Developer"]


@st.cache_data
def load_base_data():
    d = pd.read_csv(DATA / "skill_demand.csv")
    a = pd.read_csv(DATA / "curriculum_skills_pl300.csv")
    b = pd.read_csv(DATA / "curriculum_skills_ms_catalog.csv")
    a["source"] = "PL-300 (Power BI)"
    return d, pd.concat([a, b], ignore_index=True)


demand, curr = load_base_data()

if "demand" not in st.session_state:
    st.session_state.demand = demand.copy()
if "matrix" not in st.session_state:
    st.session_state.matrix = SkillGapEngineV2().run(st.session_state.demand, curr)
if "student" not in st.session_state:
    st.session_state.student = None
if "job_count" not in st.session_state:
    st.session_state.job_count = 10  # Default or dynamically updated


# 3. Pages


def dashboard_page():
    st.html(
        '''<div class="hero">
            <div class="hero-fx" aria-hidden="true">
                <span class="node n1"></span>
                <span class="node n2"></span>
                <span class="node n3"></span>
                <span class="node n4"></span>
                <span class="node n5"></span>
                <span class="beam b1"></span>
                <span class="beam b2"></span>
                <span class="beam b3"></span>
            </div>
            <h1>SkillUpIndia</h1>
            <p>Real-time skill intelligence & curriculum alignment platform</p>
        </div>'''
    )

    m = st.session_state.matrix

    cols = st.columns(4)
    with cols[0]:
        st.metric("Skills tracked", len(m))
    with cols[1]:
        high_gaps = int(m.Status.isin(["High", "Critical"]).sum())
        st.metric("High/critical gaps", high_gaps)
    with cols[2]:
        top_skill = m.iloc[0]["Market Skill"] if not m.empty else "N/A"
        st.metric("Top market skill", top_skill)
    with cols[3]:
        st.metric("Active jobs", int(st.session_state.job_count))

    st.header("High-level alignment matrix", icon=":material/grid_view:")
    st.dataframe(
        m[["Market Skill", "Industry Demand Weight", "Best Curriculum Match", "Effective Coverage", "Weighted Gap Score", "Status"]],
        width="stretch",
        hide_index=True,
    )


def market_pulse_page():
    st.header("Market pulse", icon=":material/trending_up:")
    st.caption("Explore real-time industry demand and identify the most valuable skills in the current market.")

    df_demand = st.session_state.demand.sort_values(by="demand_percentage", ascending=False).head(15)

    fig = px.bar(
        df_demand,
        x="skill_normalized",
        y="demand_percentage",
        title="Top 15 most demanded skills",
        labels={"skill_normalized": "Skill", "demand_percentage": "Demand %"},
        color="demand_percentage",
        color_continuous_scale="Blues",
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50, l=0, r=0, b=0))
    st.plotly_chart(fig, width="stretch")

    st.dataframe(st.session_state.demand, width="stretch", hide_index=True)

    csv = st.session_state.demand.to_csv(index=False).encode("utf-8")
    st.download_button("Download demand CSV", csv, "skill_demand.csv", "text/csv", icon=":material/download:")


def curriculum_audit_page():
    st.header("Curriculum audit", icon=":material/school:")

    m = st.session_state.matrix
    col1, col2 = st.columns([1, 2])
    with col1:
        st.caption("Adjust the threshold to filter for critical curriculum gaps.")
        t = st.slider("Minimum gap score", 0.0, 0.8, 0.12, 0.01)
        alignment_score = max(0, 100 - m["Weighted Gap Score"].mean() * 100)
        st.metric("Overall alignment score", f"{alignment_score:.1f}%")

    f = m[m["Weighted Gap Score"] >= t]

    st.subheader("Gap analysis matrix")
    st.dataframe(f, width="stretch", hide_index=True)
    csv = f.to_csv(index=False).encode("utf-8")
    st.download_button("Export audit report", csv, "curriculum_audit.csv", "text/csv", icon=":material/download:")


def upskill_bridge_page():
    st.header("Upskill bridge", icon=":material/route:")
    st.caption("Generate a personalized learning path based on your existing skills and the current market gaps.")

    known = st.multiselect("Select your current skills", sorted(st.session_state.demand.skill_normalized.unique()))

    if known:
        with st.spinner("Generating optimal learning path..."):
            path = LearningPathEngine().build(st.session_state.matrix, known)

        st.subheader("Your action plan")
        for i, x in enumerate(path[:15], 1):
            with st.expander(f"{i}. {x['Skill']} • Priority: {x['Priority']}"):
                st.markdown(f"**Why this matters:** {x['Why']}")
                st.markdown(f"**Action plan:** {x['Learning Action']}")

        if path:
            csv = pd.DataFrame(path).to_csv(index=False).encode("utf-8")
            st.download_button("Download learning path", csv, "learning_path.csv", "text/csv", icon=":material/download:")


def student_profile_page():
    st.header("Student profile", icon=":material/person:")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name", placeholder="e.g. John Doe")
    with col2:
        role = st.selectbox("Target role", ROLE_OPTIONS)

    skills = st.multiselect("Current skills", sorted(st.session_state.demand.skill_normalized.unique()))

    if st.button("Save profile", type="primary", icon=":material/save:") and name:
        sid = store.add_student(name, role, skills)
        st.session_state.student = {"id": sid, "name": name, "role": role, "skills": skills}
        st.toast(f"Profile saved (ID: {sid})", icon=":material/check_circle:")

    if st.session_state.student:
        st.subheader(f"Profile readiness: {st.session_state.student['name']}")

        known = {x.lower() for x in st.session_state.student["skills"]}
        tot = st.session_state.demand.demand_percentage.sum()
        covered = sum(r.demand_percentage for _, r in st.session_state.demand.iterrows() if str(r.skill_normalized).lower() in known)
        ready = covered / tot * 100 if tot else 0

        st.metric("Demand-weighted readiness", f"{ready:.1f}%")
        st.progress(min(1.0, ready / 100))

        st.markdown("#### Recommended learning path")
        path_df = pd.DataFrame(LearningPathEngine().build(st.session_state.matrix, st.session_state.student["skills"]))
        st.dataframe(path_df, width="stretch", hide_index=True)


def resume_to_profile_page():
    st.header("Resume to profile", icon=":material/description:")
    st.caption("Upload your resume to automatically extract skills and generate a personalized readiness profile.")

    u = st.file_uploader("Upload resume (PDF)", type=["pdf"])
    if u:
        with st.spinner("Analyzing resume..."):
            r = ResumeParser().parse(u)

        st.success(f"Detected {len(r['skills'])} explicit skills", icon=":material/check_circle:")
        st.info(f"**Extracted skills:** {', '.join(r['skills']) or 'None detected'}")

        path = LearningPathEngine().build(st.session_state.matrix, r["skills"])
        st.subheader("Personalized priorities")
        st.dataframe(pd.DataFrame(path), width="stretch", hide_index=True)
        st.caption("Note: extraction is based on explicit keywords. Proficiency/experience are not currently inferred.")

        st.subheader("Save as profile")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name for profile")
        with col2:
            role = st.selectbox("Target role", ROLE_OPTIONS, key="resume_role")

        if st.button("Create profile from resume", type="primary", icon=":material/person_add:") and name:
            sid = store.add_student(name, role, r["skills"])
            st.toast(f"Profile created (ID: {sid})", icon=":material/check_circle:")


def progress_tracking_page():
    st.header("Progress tracking", icon=":material/bar_chart:")

    ss = store.students()
    if not ss:
        st.warning("No student profiles found. Please create one first.", icon=":material/warning:")
        return

    opts = {f"{x[1]} • {x[2]} (ID {x[0]})": x[0] for x in ss}
    label = st.selectbox("Select student", list(opts))
    sid = opts[label]
    existing = dict(store.get_progress(sid))

    st.subheader("Track top 15 market skills")

    p = dict(store.get_progress(sid))
    completed_pct = (sum(v == "Completed" for v in p.values()) / max(1, len(p))) * 100 if p else 0

    st.progress(completed_pct / 100)
    st.metric("Completion rate", f"{completed_pct:.0f}%")

    for s in st.session_state.matrix["Market Skill"].head(15):
        old = existing.get(s, "Not Started")
        new = st.selectbox(s, ["Not Started", "Learning", "Completed"], index=["Not Started", "Learning", "Completed"].index(old), key=f"{sid}_{s}")
        if new != old:
            store.set_progress(sid, s, new)
            st.toast(f"Updated status for {s} to {new}", icon=":material/check_circle:")


def curriculum_upload_page():
    st.header("Curriculum upload", icon=":material/upload_file:")
    st.caption("Ingest course materials or syllabus documents to cross-reference against market demand.")

    u = st.file_uploader("Upload curriculum document (PDF)", type=["pdf"])
    if u:
        with st.spinner("Parsing curriculum..."):
            text, skills = CurriculumPDFParser().parse(u)

        st.success(f"Detected {len(skills)} supported skills", icon=":material/check_circle:")
        st.info(f"**Extracted topics:** {', '.join(skills) or 'None detected'}")

        if skills:
            c = pd.DataFrame({"Skill": skills, "DepthWeight": [0.65] * len(skills), "source": ["Uploaded Curriculum"] * len(skills)})
            m = SkillGapEngineV2().run(st.session_state.demand, c)
            st.subheader("Real-time gap analysis")
            st.dataframe(m, width="stretch", hide_index=True)


def data_ingestion_page():
    st.header("Live data ingestion", icon=":material/bolt:")

    tab1, tab2 = st.tabs(["Job description text", "CSV dataset upload"])
    ing = JobPostingIngestor()
    jobs = []

    with tab1:
        st.caption("Paste a raw job description to instantly extract required skills and adjust the market baseline.")
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job title", "Data Analyst")
        with col2:
            company = st.text_input("Company", placeholder="e.g. Acme Corp")

        desc = st.text_area("Job description", height=200, placeholder="Paste job description here...")
        if st.button("Extract & ingest", type="primary", icon=":material/bolt:"):
            with st.spinner("Extracting skills via NLP..."):
                jobs = ing.from_text(desc, title, company)

    with tab2:
        st.caption("Upload a batch of job postings to bulk-update the market pulse.")
        u = st.file_uploader("Upload job CSV", type=["csv"])
        if u and st.button("Ingest CSV batch", type="primary", icon=":material/upload:"):
            with st.spinner("Processing CSV..."):
                jobs = ing.from_csv(u)

    if jobs:
        jobs = ing.normalize_jobs(jobs)
        st.session_state.demand = ing.demand(jobs)
        st.session_state.matrix = SkillGapEngineV2().run(st.session_state.demand, curr)
        st.session_state.job_count = len(jobs)
        st.success(f"Successfully ingested and processed {len(jobs)} jobs!", icon=":material/check_circle:")

        st.subheader("Extracted job data")
        df_jobs = pd.DataFrame([{"Job ID": j["job_id"], "Title": j["title"], "Company": j["company"], "Skills": ", ".join(j["skills"])} for j in jobs])
        st.dataframe(df_jobs, width="stretch", hide_index=True)


# 4. Navigation
pg = st.navigation(
    [
        st.Page(dashboard_page, title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page(market_pulse_page, title="Market pulse", icon=":material/trending_up:"),
        st.Page(curriculum_audit_page, title="Curriculum audit", icon=":material/school:"),
        st.Page(upskill_bridge_page, title="Upskill bridge", icon=":material/route:"),
        st.Page(student_profile_page, title="Student profile", icon=":material/person:"),
        st.Page(resume_to_profile_page, title="Resume to profile", icon=":material/description:"),
        st.Page(progress_tracking_page, title="Progress tracking", icon=":material/bar_chart:"),
        st.Page(curriculum_upload_page, title="Curriculum upload", icon=":material/upload_file:"),
        st.Page(data_ingestion_page, title="Data ingestion", icon=":material/bolt:"),
    ]
)

with st.sidebar:
    st.caption("SIH26134 • Skill intelligence platform")

pg.run()
