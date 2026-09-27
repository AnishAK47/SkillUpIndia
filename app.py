import json
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st
from pathlib import Path
import plotly.express as px
from engine.job_ingestor import JobPostingIngestor
from engine.resume_parser import ResumeParser
from engine.gap_engine import SkillGapEngineV2
from engine.learning_path import LearningPathEngine
from engine.data_store import SkillUpStore, SupabaseStore
from engine.curriculum_parser import CurriculumPDFParser

# 1. Page configuration
# Colors, fonts, radius, and button styling live in .streamlit/config.toml so
# they stay consistent across every native widget and survive Streamlit upgrades.
st.set_page_config(page_title="SkillUpIndia", page_icon=":material/target:", layout="wide", initial_sidebar_state="expanded")

# The app ships a single dark theme (.streamlit/config.toml), so this CSS is
# written for dark only; nothing here depends on the visitor's system theme.
# Never write a literal HTML tag (even inside a /* comment */) in this CSS:
# st.html's sanitizer doesn't understand CSS context and drops the whole block.
st.html("""<style>
/* The looping brand video (rendered below with st.video) is the page
   background. */
[data-testid="stApp"] {
    background: transparent;
}
/* The keyed container is pinned behind all content; its tint keeps text and
   charts readable over the brightest frames. Its own fill shows if the video
   is hidden for reduced motion. */
[data-testid="stLayoutWrapper"]:has(> .st-key-bg_video) {
    position: absolute;
}
.st-key-bg_video {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background: #0b0b18;
}
.st-key-bg_video video {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    object-fit: cover;
}
.st-key-bg_video::after {
    content: "";
    position: absolute;
    inset: 0;
    background: rgba(11, 11, 24, 0.6);
}
@media (prefers-reduced-motion: reduce) {
    .st-key-bg_video video { display: none; }
}
/* The hero is a glass panel so the video reads through it. */
.hero {
    background: rgba(15, 13, 32, 0.42);
    border: 1px solid rgba(165, 180, 252, 0.16);
    backdrop-filter: blur(12px) saturate(140%);
    -webkit-backdrop-filter: blur(12px) saturate(140%);
}

/* Frosted-glass cards over the video: metric tiles, expanders, and the
   dashboard panels (targeted by their container keys). */
[data-testid="stMetric"],
[data-testid="stExpander"] details,
.st-key-coverage_card,
.st-key-action_feed,
.st-key-pulse_card {
    background: rgba(21, 19, 40, 0.55);
    border-color: rgba(165, 180, 252, 0.14) !important;
    backdrop-filter: blur(14px) saturate(140%);
    -webkit-backdrop-filter: blur(14px) saturate(140%);
}

/* A dashed, glassy dropzone reads as a drop target rather than a flat box. */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(21, 19, 40, 0.55);
    border: 1.5px dashed rgba(165, 180, 252, 0.35);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    transition: border-color 0.2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #818cf8;
}

/* Frosted top bar: the header also holds the top navigation and the main
   menu, so it is restyled rather than hidden; content scrolls under glass. */
[data-testid="stHeader"] {
    background: rgba(11, 11, 24, 0.72);
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    border-bottom: 1px solid rgba(165, 180, 252, 0.14);
}

/* Start content just below the 3.75rem header instead of 7.5rem down.
   Side gutters are left at Streamlit's defaults for readable line lengths. */
[data-testid="stMainBlockContainer"] {
    padding-top: 5rem;
    padding-bottom: 3rem;
}
.hero {
    padding: 3rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 2rem;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        0 20px 40px -12px rgba(76, 29, 149, 0.35);
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

[data-testid="stMetric"] {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 25px -10px rgba(124, 58, 237, 0.35);
}

/* Primary actions get a saffron accent, kept apart from the indigo brand
   colour that marks state (focus, sliders, links). The deep end of the
   gradient keeps white label text above 4.5:1 contrast in both themes. */
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    background: linear-gradient(135deg, #c2410c 0%, #9a3412 100%);
    border: none;
    color: #ffffff;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    transition: transform 0.15s ease, box-shadow 0.2s ease;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: linear-gradient(135deg, #c2410c 0%, #9a3412 100%);
    border: none;
    color: #ffffff;
    transform: translateY(-1px);
    box-shadow: 0 8px 22px -6px rgba(234, 88, 12, 0.55);
}
[data-testid="stBaseButton-primary"]:active,
[data-testid="stBaseButton-primaryFormSubmit"]:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px -2px rgba(234, 88, 12, 0.4);
}
[data-testid="stBaseButton-primary"]:focus-visible,
[data-testid="stBaseButton-primaryFormSubmit"]:focus-visible {
    outline: 2px solid #fb923c;
    outline-offset: 2px;
}
[data-testid="stBaseButton-primary"]:disabled,
[data-testid="stBaseButton-primaryFormSubmit"]:disabled {
    opacity: 0.5;
    transform: none;
    box-shadow: none;
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primaryFormSubmit"] { transition: none; }
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover { transform: none; }
}
.hero .hero-tag {
    display: inline-block;
    margin-bottom: 1rem;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #e0e7ff;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.18);
    position: relative;
    z-index: 2;
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


@st.cache_resource
def get_store():
    """Supabase when [supabase] secrets are set (data survives restarts), else local SQLite."""
    try:
        supabase = st.secrets["supabase"]
        return SupabaseStore(supabase["url"], supabase["service_role_key"])
    except (KeyError, FileNotFoundError):
        return SkillUpStore(str(BASE / "skillupindia.db"))


store = get_store()


def auth_configured():
    try:
        return "auth" in st.secrets
    except FileNotFoundError:
        return False


def admin_emails():
    try:
        return {email.strip().lower() for email in st.secrets["access"]["admins"]}
    except (KeyError, FileNotFoundError):
        return set()


def current_user():
    """The signed-in user as a dict, or None.

    Admin requires a verified email on the allowlist: email/password sign-ups
    can claim any address until it's verified.
    """
    if not auth_configured() or not st.user.is_logged_in:
        return None
    email = str(st.user.get("email") or "").lower()
    verified = st.user.get("email_verified") is True
    return {
        "id": st.user.get("sub"),
        "email": email,
        "name": st.user.get("name") or email,
        "verified": verified,
        "admin": verified and email in admin_emails(),
    }


USER = current_user()


def sign_in_prompt(action):
    with st.container(border=True):
        st.markdown(f":material/lock: **Sign in to {action}.** Browsing doesn't need an account.")
        if auth_configured():
            if st.button("Sign in or create an account", icon=":material/login:", key=f"sign_in_{action}"):
                st.login()
        else:
            st.caption("Sign-in isn't set up on this deployment yet.")

# st.video serves the file from a cacheable URL once, instead of re-sending
# a Base64 copy on every rerun; the CSS above pins it behind the page.
with st.container(key="bg_video"):
    # Crossfaded to loop seamlessly; regenerate with scripts/make_bg_loop.py.
    st.video(str(BASE / "assets" / "skillup_bg_loop.mp4"), autoplay=True, loop=True, muted=True)
    # st.video has no playsinline option, and iPhones won't autoplay inline
    # without it. The pause listener resumes playback if a rerun pauses the
    # video while the page is visible; the retries cover late mounting.
    st.html(
        """<script>
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const fixBg = () => document.querySelectorAll(".st-key-bg_video video").forEach((v) => {
            v.muted = true;
            v.playsInline = true;
            v.setAttribute("playsinline", "");
            v.controls = false;
            if (reduceMotion) { v.pause(); return; }
            if (!v.dataset.keepAlive) {
                v.dataset.keepAlive = "1";
                v.addEventListener("pause", () => { if (!document.hidden) v.play().catch(() => {}); });
            }
            if (v.paused && !document.hidden) v.play().catch(() => {});
        });
        [0, 500, 2000].forEach((ms) => setTimeout(fixBg, ms));
        document.addEventListener("visibilitychange", fixBg);
        </script>""",
        unsafe_allow_javascript=True,
    )

ROLE_OPTIONS = ["Data Analyst", "Business Analyst", "Data Engineer", "Power BI Developer"]

# st.dataframe paints cells on a canvas, so CSS can't reach them: column_config
# is the styling hook. Demand/coverage bars reuse the dashboard chart colours.
GAP_COLUMNS = {
    "Market Skill": st.column_config.TextColumn("Skill", pinned=True),
    "Industry Demand Weight": st.column_config.ProgressColumn(
        "Demand", min_value=0, max_value=1, format="%.2f",
        help="Share of analysed job postings that ask for this skill."),
    "Best Curriculum Match": st.column_config.TextColumn("Best curriculum match"),
    "Match Score": st.column_config.NumberColumn(
        "Match", format="%.2f",
        help="Match strength to the closest curriculum topic: 1 exact, 0.75 partial, 0 none."),
    "Curriculum Depth Weight": st.column_config.NumberColumn(
        "Depth", format="%.2f", help="How deeply the matched topic is taught."),
    "Effective Coverage": st.column_config.ProgressColumn(
        "Coverage", min_value=0, max_value=1, format="%.2f",
        color="#22d3ee",
        help="Match x depth: how well the curriculum covers this skill."),
    "Source Framework": st.column_config.TextColumn("Source"),
    "Weighted Gap Score": st.column_config.NumberColumn(
        "Gap score", format="%.2f",
        help="Demand x (1 - coverage). 0.12+ Moderate, 0.25+ High, 0.40+ Critical."),
    "Status": st.column_config.TextColumn("Status"),
}
_STATUS_COLORS = {"Critical": "#f87171", "High": "#fb923c", "Moderate": "#fbbf24", "Low": "#4ade80"}


def gap_table(df):
    st.dataframe(
        df.style.map(lambda s: f"color: {_STATUS_COLORS.get(s, 'inherit')}; font-weight: 600", subset=["Status"]),
        column_config=GAP_COLUMNS,
        hide_index=True,
        width="stretch",
    )


FEEDBACK_AREAS = ["Skill extraction", "Skills alignment", "Something else"]
FEEDBACK_AREA_HELP = {
    "Skill extraction": "A skill was missed or wrongly detected in a resume, job description, or syllabus.",
    "Skills alignment": "A curriculum match, coverage value, or gap score looks wrong.",
    "Something else": "Any other bug or suggestion.",
}
FEEDBACK_PAGES = [
    "Dashboard", "Market pulse", "Data ingestion", "Curriculum audit", "Curriculum upload",
    "Student profile", "Resume to profile", "Upskill bridge", "Progress tracking", "Other",
]
FEEDBACK_LIMIT = 5  # submissions per browser session, to deter spam


def github_issue_settings():
    """(token, repo) from st.secrets["github"], or None when not configured."""
    try:
        gh = st.secrets["github"]
        return gh["token"], gh["repo"]
    except (KeyError, FileNotFoundError):
        return None


def open_github_issue(title, body):
    """Open an issue on the configured repo; return its URL, or None if that isn't possible."""
    settings = github_issue_settings()
    if settings is None:
        return None
    token, repo = settings
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps({"title": title, "body": body, "labels": ["feedback"]}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)["html_url"]
    except (urllib.error.URLError, KeyError, ValueError):
        return None


def feedback_link(area, page):
    st.page_link(
        FEEDBACK_PAGE, label="Something wrong here? Report it", icon=":material/flag:",
        query_params={"area": area, "page": page},
    )


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
            <span class="hero-tag">SIH26134 · Smart India Hackathon</span>
            <h1>SkillUpIndia</h1>
            <p>Real-time skill intelligence & curriculum alignment platform</p>
        </div>'''
    )

    m = st.session_state.matrix
    open_gaps = m[m.Status.isin(["Critical", "High"])]
    alignment = max(0, 100 - m["Weighted Gap Score"].mean() * 100) if not m.empty else 0

    cols = st.columns(4)
    with cols[0]:
        st.metric("Skills tracked", len(m), icon=":material/insights:", border=True,
                  help="Distinct market skills extracted from the analysed job postings.")
    with cols[1]:
        st.metric("Critical & high gaps", len(open_gaps), icon=":material/warning:", border=True,
                  help="Skills whose weighted gap score is 0.25 or higher.")
    with cols[2]:
        st.metric("Curriculum alignment", f"{alignment:.0f}%", icon=":material/verified:", border=True,
                  help="100% minus the average weighted gap score across all tracked skills.")
    with cols[3]:
        st.metric("Job postings analysed", int(st.session_state.job_count), icon=":material/work:", border=True,
                  help="Postings behind the current demand baseline. Update it from Data ingestion.")

    chart_col, feed_col = st.columns([7, 3])

    with chart_col, st.container(border=True, key="coverage_card"):
        st.subheader("Demand vs curriculum coverage", icon=":material/stacked_bar_chart:")
        top = m.nlargest(10, "Industry Demand Weight")
        long = top.melt(
            id_vars="Market Skill",
            value_vars=["Industry Demand Weight", "Effective Coverage"],
            var_name="Measure",
            value_name="Score",
        )
        long["Measure"] = long["Measure"].map({"Industry Demand Weight": "Demand", "Effective Coverage": "Coverage"})
        fig = px.bar(
            long, x="Score", y="Market Skill", color="Measure", barmode="group", orientation="h",
            color_discrete_map={"Demand": "#818cf8", "Coverage": "#22d3ee"},
        )
        fig.update_layout(
            height=380,
            margin=dict(t=10, l=16, r=0, b=0),
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right", title=None),
            yaxis=dict(title=None, autorange="reversed"),
            xaxis=dict(title=None, range=[0, 1]),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

    with feed_col, st.container(border=True, key="action_feed"):
        st.subheader("Action items", icon=":material/task_alt:")
        badge = {"Critical": ":red-badge[Critical]", "High": ":orange-badge[High]", "Moderate": ":yellow-badge[Moderate]"}
        items = m[m.Status != "Low"].sort_values("Weighted Gap Score", ascending=False)
        # Scroll only once the list outgrows the chart beside it; a fixed-height
        # box around two or three items just reads as empty space.
        with st.container(height=380 if len(items) > 5 else "content", border=False):
            if items.empty:
                st.caption("No open gaps. The curriculum covers current demand.")
            for _, r in items.iterrows():
                match = r["Best Curriculum Match"]
                fix = "Add a module: no curriculum match" if str(match) in ("None", "nan", "") else f"Deepen coverage in {match}"
                st.markdown(f"{badge[r.Status]} **{r['Market Skill']}**  \n{fix} · gap {r['Weighted Gap Score']:.2f}")
        covered = int((m.Status == "Low").sum())
        st.caption(f":material/check_circle: {covered} of {len(m)} skills are well covered.")

    with st.expander("Full alignment matrix", icon=":material/table:"):
        gap_table(m[["Market Skill", "Industry Demand Weight", "Best Curriculum Match", "Effective Coverage", "Weighted Gap Score", "Status"]])


def market_pulse_page():
    st.header("Market pulse", icon=":material/trending_up:")
    st.caption("Explore real-time industry demand and identify the most valuable skills in the current market.")

    df_demand = st.session_state.demand.sort_values(by="demand_percentage", ascending=False).head(15)

    with st.container(border=True, key="pulse_card"):
        st.subheader("Top 15 most demanded skills", icon=":material/leaderboard:")
        fig = px.bar(
            df_demand,
            x="demand_percentage",
            y="skill_normalized",
            orientation="h",
            text="demand_percentage",
            labels={"skill_normalized": "Skill", "demand_percentage": "Demand %"},
            color_discrete_sequence=["#818cf8"],
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False)
        fig.update_layout(
            height=460,
            margin=dict(t=10, l=16, r=30, b=0),
            yaxis=dict(title=None, autorange="reversed"),
            xaxis=dict(title=None, showticklabels=False, showgrid=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        st.session_state.demand,
        column_config={
            "skill_normalized": st.column_config.TextColumn("Skill"),
            "job_count": st.column_config.NumberColumn("Postings", help="Job postings that mention this skill."),
            "demand_percentage": st.column_config.ProgressColumn(
                "Demand", min_value=0, max_value=100, format="%d%%",
                help="Share of analysed job postings that ask for this skill."),
        },
        width="stretch",
        hide_index=True,
    )

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
        st.metric("Overall alignment score", f"{alignment_score:.1f}%", icon=":material/verified:", border=True)

    f = m[m["Weighted Gap Score"] >= t]

    st.subheader("Gap analysis matrix")
    gap_table(f)
    csv = f.to_csv(index=False).encode("utf-8")
    st.download_button("Export audit report", csv, "curriculum_audit.csv", "text/csv", icon=":material/download:")
    feedback_link("Skills alignment", "Curriculum audit")


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

    if USER:
        if st.button("Save profile", type="primary", icon=":material/save:") and name:
            sid = store.add_student(USER["id"], USER["email"], name, role, skills)
            st.session_state.student = {"id": sid, "name": name, "role": role, "skills": skills}
            st.toast(f"Profile saved (ID: {sid})", icon=":material/check_circle:")
    else:
        # Signed-out visitors can still preview readiness; only saving needs an account.
        if st.button("Check readiness", type="primary", icon=":material/speed:") and name:
            st.session_state.student = {"id": None, "name": name, "role": role, "skills": skills}
        sign_in_prompt("save this profile and track progress")

    if st.session_state.student:
        st.subheader(f"Profile readiness: {st.session_state.student['name']}")

        known = {x.lower() for x in st.session_state.student["skills"]}
        tot = st.session_state.demand.demand_percentage.sum()
        covered = sum(r.demand_percentage for _, r in st.session_state.demand.iterrows() if str(r.skill_normalized).lower() in known)
        ready = covered / tot * 100 if tot else 0

        st.metric("Demand-weighted readiness", f"{ready:.1f}%", icon=":material/speed:", border=True)
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
        feedback_link("Skill extraction", "Resume to profile")

        path = LearningPathEngine().build(st.session_state.matrix, r["skills"])
        st.subheader("Personalized priorities")
        st.dataframe(pd.DataFrame(path), width="stretch", hide_index=True)
        st.caption("Note: extraction is based on explicit keywords. Proficiency/experience are not currently inferred.")

        st.subheader("Save as profile")
        if not USER:
            sign_in_prompt("save this resume as a profile")
            return
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name for profile")
        with col2:
            role = st.selectbox("Target role", ROLE_OPTIONS, key="resume_role")

        if st.button("Create profile from resume", type="primary", icon=":material/person_add:") and name:
            sid = store.add_student(USER["id"], USER["email"], name, role, r["skills"])
            st.toast(f"Profile created (ID: {sid})", icon=":material/check_circle:")


def progress_tracking_page():
    st.header("Progress tracking", icon=":material/bar_chart:")

    if not USER:
        sign_in_prompt("track progress on your saved profiles")
        return

    # Members see only their own profiles; admins see everyone's, labelled by owner.
    profiles = store.students(None if USER["admin"] else USER["id"])
    if not profiles:
        st.info("You haven't saved a profile yet. Create one on the Student profile page.", icon=":material/info:")
        return

    def profile_label(p):
        owner = f" · {p['owner_email']}" if USER["admin"] and p.get("owner_email") else ""
        return f"{p['name']} • {p['target_role']}{owner} (ID {p['id']})"

    opts = {profile_label(p): p["id"] for p in profiles}
    label = st.selectbox("Select profile" if not USER["admin"] else "Select student", list(opts))
    sid = opts[label]
    existing = dict(store.get_progress(sid))

    st.subheader("Track top 15 market skills")

    p = dict(store.get_progress(sid))
    completed_pct = (sum(v == "Completed" for v in p.values()) / max(1, len(p))) * 100 if p else 0

    st.progress(completed_pct / 100)
    st.metric("Completion rate", f"{completed_pct:.0f}%", icon=":material/task_alt:", border=True)

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
        feedback_link("Skill extraction", "Curriculum upload")

        if skills:
            c = pd.DataFrame({"Skill": skills, "DepthWeight": [0.65] * len(skills), "source": ["Uploaded Curriculum"] * len(skills)})
            m = SkillGapEngineV2().run(st.session_state.demand, c)
            st.subheader("Real-time gap analysis")
            gap_table(m)


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
            with st.spinner("Matching skills in the job description..."):
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
        feedback_link("Skill extraction", "Data ingestion")


def feedback_page():
    st.header("Feedback", icon=":material/feedback:")
    st.caption("Spotted a skill the parser missed or misread, or a curriculum match that looks wrong? Tell us here.")

    area = st.segmented_control(
        "What is it about?", FEEDBACK_AREAS, default=FEEDBACK_AREAS[0], required=True,
        key="area", bind="query-params",
    )
    st.caption(FEEDBACK_AREA_HELP[area])
    page = st.selectbox("Where did it happen?", FEEDBACK_PAGES, key="page", bind="query-params")

    if not USER:
        sign_in_prompt("send feedback")
        return

    posts_publicly = github_issue_settings() is not None
    with st.form("feedback_form", clear_on_submit=True):
        skill = st.text_input("Skill involved (optional)", placeholder="e.g. Power BI", max_chars=60)
        details = st.text_area(
            "What happened?", max_chars=2000,
            placeholder="e.g. My resume says 'PowerBI' but Power BI wasn't detected.",
        )
        expected = st.text_area("What did you expect? (optional)", max_chars=1000)
        if posts_publicly:
            st.caption(":material/public: Feedback is posted as a public GitHub issue. Don't include personal details.")
        sent = st.form_submit_button("Send feedback", type="primary", icon=":material/send:")

    if sent:
        sent_so_far = st.session_state.get("feedback_sent", 0)
        details, skill, expected = details.strip(), skill.strip(), expected.strip()
        if not details:
            st.error("Please describe what happened.", icon=":material/error:")
        elif sent_so_far >= FEEDBACK_LIMIT:
            st.warning(f"You've sent {FEEDBACK_LIMIT} reports this session. Thanks! Please try again later.", icon=":material/hourglass:")
        else:
            title = f"[{area}] {page}: {details.splitlines()[0][:70]}"
            body = (
                f"**Area:** {area}  \n**Page:** {page}  \n**Skill:** {skill or '-'}\n\n"
                f"**What happened**\n\n{details}\n\n**Expected**\n\n{expected or '-'}\n\n"
                "_Submitted from the SkillUpIndia feedback form._"
            )
            # The reporter's email is kept in the database only, never in the public issue.
            issue_url = open_github_issue(title, body)
            store.add_feedback(area, page, skill, details, expected, issue_url, USER["email"])
            st.session_state.feedback_sent = sent_so_far + 1
            if issue_url:
                st.success(f"Thanks! Logged as [a GitHub issue]({issue_url}).", icon=":material/check_circle:")
            elif posts_publicly:
                st.warning("Thanks! Saved here, but it couldn't be sent to GitHub right now.", icon=":material/cloud_off:")
            else:
                st.success("Thanks! Your feedback has been saved.", icon=":material/check_circle:")

    if not USER["admin"]:
        return
    rows = store.feedback()
    with st.expander(f"Feedback inbox ({len(rows)})", icon=":material/inbox:"):
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                column_config={
                    "created_at": st.column_config.TextColumn("Submitted"),
                    "user_email": st.column_config.TextColumn("From"),
                    "area": st.column_config.TextColumn("Area"),
                    "page": st.column_config.TextColumn("Page"),
                    "skill": st.column_config.TextColumn("Skill"),
                    "details": st.column_config.TextColumn("What happened"),
                    "expected": st.column_config.TextColumn("Expected"),
                    "issue_url": st.column_config.LinkColumn("Issue", display_text="Open"),
                },
                hide_index=True,
                width="stretch",
            )
        else:
            st.caption("No feedback yet.")


def account_page():
    st.header("Account", icon=":material/account_circle:")

    if USER:
        with st.container(border=True):
            st.markdown(f"**{USER['name']}**  \n{USER['email']}")
            if USER["admin"]:
                st.badge("Admin", icon=":material/shield_person:", color="violet")
            else:
                st.badge("Member", icon=":material/person:", color="blue")
        if not USER["verified"]:
            st.warning("Your email isn't verified yet. Use the link in the verification email, then sign in again.", icon=":material/mark_email_unread:")
        if USER["admin"]:
            st.caption("As an admin you can use Data ingestion and Curriculum upload, see every student profile, and read the feedback inbox.")
        else:
            st.caption("You can save student profiles, track their progress, and send feedback. Your profiles are visible only to you and the admins.")
        if st.button("Sign out", icon=":material/logout:"):
            st.logout()
    elif auth_configured():
        st.write("Sign in to save student profiles, track progress, and send feedback. Browsing the dashboards doesn't need an account.")
        if st.button("Sign in or create an account", type="primary", icon=":material/login:"):
            st.login()
        st.caption("Continue with Google, or use an email and password.")
    else:
        st.info("Sign-in isn't set up on this deployment yet, so profiles, progress, and feedback can't be saved.", icon=":material/info:")


# 4. Navigation
# Pages are grouped into the three portals in a top bar rather than st.tabs:
# each page keeps its own URL and only the active one executes. Admin-only pages
# are registered only for admins, so other visitors can't reach them by URL.
FEEDBACK_PAGE = st.Page(feedback_page, title="Feedback", icon=":material/feedback:", url_path="feedback")
ACCOUNT_PAGE = st.Page(
    account_page,
    title=(USER["name"] or "Account").split()[0] if USER else "Sign in",
    icon=":material/account_circle:" if USER else ":material/login:",
    url_path="account",
)
government = [st.Page(market_pulse_page, title="Market pulse", icon=":material/trending_up:", url_path="market-pulse")]
institutions = [st.Page(curriculum_audit_page, title="Curriculum audit", icon=":material/school:", url_path="curriculum-audit")]
if USER and USER["admin"]:
    government.append(st.Page(data_ingestion_page, title="Data ingestion", icon=":material/bolt:", url_path="data-ingestion"))
    institutions.append(st.Page(curriculum_upload_page, title="Curriculum upload", icon=":material/upload_file:", url_path="curriculum-upload"))

pg = st.navigation(
    {
        "": [
            st.Page(dashboard_page, title="Dashboard", icon=":material/dashboard:", default=True),
        ],
        "Government": government,
        "Institutions": institutions,
        "Students": [
            st.Page(student_profile_page, title="Student profile", icon=":material/person:", url_path="student-profile"),
            st.Page(resume_to_profile_page, title="Resume to profile", icon=":material/description:", url_path="resume-to-profile"),
            st.Page(upskill_bridge_page, title="Upskill bridge", icon=":material/route:", url_path="upskill-bridge"),
            st.Page(progress_tracking_page, title="Progress tracking", icon=":material/bar_chart:", url_path="progress-tracking"),
        ],
        "Account": [ACCOUNT_PAGE, FEEDBACK_PAGE],
    },
    position="top",
)

pg.run()
