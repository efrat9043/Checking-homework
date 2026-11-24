"""
העיצוב של הממשק: גופן עברי, כיוון ימין-לשמאל, כרטיסים, תגיות וצבעים.
כל ה-CSS נמצא כאן, כדי שקבצי המסכים יכילו רק תוכן.
"""
import streamlit as st

# צבעי המותג (משמשים גם בגרף)
BRAND = "#4F46E5"
INK = "#1E2235"
MUTED = "#6B7280"
LINE = "#E6E8F0"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');

:root {
  --brand: #4F46E5; --brand-2: #7C3AED; --brand-soft: #EEF0FF;
  --ink: #1E2235; --muted: #6B7280; --line: #E6E8F0; --card: #FFFFFF; --bg: #F6F7FB;
  --good: #047857; --good-soft: #E7F6EF;
  --mid: #B45309;  --mid-soft: #FDF3E4;
  --low: #B91C1C;  --low-soft: #FDECEC;
  --info: #1D4ED8; --info-soft: #E8EFFE;
  --radius: 16px; --shadow: 0 1px 2px rgba(16,24,40,.04), 0 6px 24px rgba(16,24,40,.06);
}

/* גופן עברי לכל האפליקציה, בלי לשבור את האייקונים של Streamlit */
.stApp, .stApp * { font-family: 'Heebo', system-ui, sans-serif; }
[data-testid="stIconMaterial"], .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; }

/* ימין לשמאל */
.stApp { direction: rtl; background: var(--bg); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label { text-align: right; }
/* קוד וטבלאות נשארים משמאל לימין */
pre, code, [data-testid="stCode"], [data-testid="stDataFrame"], [data-testid="stDataEditor"] { direction: ltr; text-align: left; }
textarea { direction: rtl; }

.block-container { padding-top: 1.2rem; padding-bottom: 4rem; max-width: 1240px; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* ---------- כותרת עליונה ---------- */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--brand), var(--brand-2)); color: #fff; font-weight: 800; font-size: 20px;
  box-shadow: 0 6px 18px rgba(79,70,229,.35); }
.brand-name { font-size: 22px; font-weight: 800; color: var(--ink); line-height: 1.1; }
.brand-sub { font-size: 13px; color: var(--muted); }

/* ---------- שלבים ---------- */
.stepper { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.step { display: flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px;
  background: #fff; border: 1px solid var(--line); color: var(--muted); font-size: 13.5px; font-weight: 500; }
.step .num { width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center;
  background: var(--bg); font-size: 12px; font-weight: 700; }
.step.active { border-color: var(--brand); color: var(--brand); background: var(--brand-soft); }
.step.active .num { background: var(--brand); color: #fff; }
.step.done { color: var(--good); }
.step.done .num { background: var(--good-soft); color: var(--good); }
.step-sep { width: 18px; height: 1px; background: var(--line); }

/* ---------- כרטיס פתיחה ---------- */
.hero { border-radius: 22px; padding: 30px 34px; margin: 4px 0 22px; color: #fff;
  background: radial-gradient(1200px 300px at 100% 0%, rgba(255,255,255,.18), transparent 60%),
              linear-gradient(120deg, #4338CA 0%, #6D28D9 60%, #7C3AED 100%);
  box-shadow: 0 18px 40px rgba(67,56,202,.25); }
.hero h1 { color: #fff; font-size: 30px; font-weight: 800; margin: 0 0 6px; padding: 0; }
.hero p { color: rgba(255,255,255,.88); font-size: 16px; margin: 0; }
.hero.success { background: linear-gradient(120deg, #047857 0%, #059669 55%, #10B981 100%);
  box-shadow: 0 18px 40px rgba(5,150,105,.25); }

/* ---------- כרטיסים ---------- */
.card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 18px 20px; }
.card-title { font-weight: 700; color: var(--ink); font-size: 16px; margin-bottom: 4px; }
.card-sub { color: var(--muted); font-size: 13.5px; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: var(--radius) !important; background: var(--card);
  box-shadow: var(--shadow); }

/* ---------- כרטיסי מספרים ---------- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin: 6px 0 18px; }
.stat { background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 18px; box-shadow: var(--shadow); }
.stat .label { color: var(--muted); font-size: 13px; font-weight: 500; }
.stat .value { color: var(--ink); font-size: 30px; font-weight: 800; line-height: 1.15; margin-top: 4px; }
.stat .hint { color: var(--muted); font-size: 12.5px; margin-top: 2px; }
.stat.accent { background: linear-gradient(135deg, var(--brand-soft), #fff); border-color: #D9DBFF; }

/* ---------- תגיות ---------- */
.chip { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px;
  font-size: 12.5px; font-weight: 600; margin: 2px 0 2px 6px; border: 1px solid transparent; }
.chip.bad  { background: var(--low-soft);  color: var(--low);  border-color: #F6CACA; }
.chip.warn { background: var(--mid-soft);  color: var(--mid);  border-color: #F3D9B1; }
.chip.info { background: var(--info-soft); color: var(--info); border-color: #C9D8FB; }
.chip.ok   { background: var(--good-soft); color: var(--good); border-color: #BFE6D3; }

/* ---------- ציון ---------- */
.score { display: inline-flex; align-items: baseline; gap: 4px; padding: 4px 12px; border-radius: 12px; font-weight: 800; font-size: 20px; }
.score small { font-size: 12px; font-weight: 600; opacity: .8; }
.score.good { background: var(--good-soft); color: var(--good); }
.score.mid  { background: var(--mid-soft);  color: var(--mid); }
.score.low  { background: var(--low-soft);  color: var(--low); }

/* ---------- שאלה בדף תלמידה ---------- */
.q-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.q-title { font-weight: 700; color: var(--ink); }
.q-points { font-weight: 700; color: var(--brand); }
.crit { padding: 8px 0; border-bottom: 1px dashed var(--line); }
.crit:last-child { border-bottom: none; }
.crit-name { font-weight: 600; color: var(--ink); }
.crit-pts { color: var(--brand); font-weight: 700; font-size: 13px; }
.crit-desc { color: var(--muted); font-size: 13.5px; margin-top: 2px; }

/* ---------- יומן התקדמות ---------- */
.log { font-size: 14px; color: var(--ink); }
.log-row { display: flex; gap: 10px; align-items: center; padding: 7px 0; border-bottom: 1px solid #F0F1F6; }
.log-row:last-child { border-bottom: none; }
.log-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand); flex: none; }
.log-time { color: var(--muted); font-size: 12px; margin-inline-start: auto; direction: ltr; }
.now { display: flex; align-items: center; gap: 14px; }
.now-avatar { width: 52px; height: 52px; border-radius: 14px; background: var(--brand-soft); color: var(--brand);
  display: grid; place-items: center; font-weight: 800; font-size: 20px; }
.now-name { font-size: 20px; font-weight: 800; color: var(--ink); }
.now-step { color: var(--muted); font-size: 14px; }
.pulse { animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .45; } }

/* ---------- רשימת קבצים ---------- */
.file-row { display: flex; align-items: center; gap: 10px; padding: 7px 10px; border-radius: 10px; }
.file-row:nth-child(odd) { background: #F8F9FC; }
.file-ext { font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: var(--brand-soft); color: var(--brand); direction: ltr; }
.file-name { font-weight: 500; color: var(--ink); }

/* ---------- כפתורים ---------- */
.stButton > button, .stDownloadButton > button { border-radius: 12px; font-weight: 600; padding: .55rem 1.1rem; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--brand), var(--brand-2)); border: none; box-shadow: 0 6px 18px rgba(79,70,229,.28); }
.stButton > button[kind="primary"]:hover { filter: brightness(1.06); }

/* ---------- לשוניות ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-weight: 600; padding: 10px 16px; }

.muted { color: var(--muted); }
.section-title { font-size: 18px; font-weight: 800; color: var(--ink); margin: 6px 0 10px; }
</style>
"""


def inject():
    """מזריק את ה-CSS לדף. נקרא פעם אחת בכל הרצה של app.py."""
    st.markdown(_CSS, unsafe_allow_html=True)
