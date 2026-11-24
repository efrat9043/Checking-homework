"""מסך 2: התקדמות הבדיקה בזמן אמת – מי נבדקת עכשיו, כמה נשארו, ומה המערכת עושה."""
import copy
from datetime import datetime

import streamlit as st

from ui import components as c
from ui import state

TITLES = {
    "initial": ("הבדיקה בעיצומה", "המערכת בונה מחוון ובודקת כל עבודה. אפשר להשאיר את החלון פתוח."),
    "recheck": ("בדיקה חוזרת", "בודקת שוב את העבודות שסימנת. כל השאר נשאר כמו שהיה."),
    "regrade": ("בדיקה מחדש לפי המחוון החדש", "כל הכיתה נבדקת שוב לפי המחוון שערכת."),
    "finalize": ("יוצרת את דפי המשוב", "הנתונים שאישרת נשמרים לקובץ נפרד לכל תלמידה."),
}


def render():
    ss = st.session_state
    title, subtitle = TITLES.get(ss.run_kind, TITLES["initial"])
    c.hero(title, subtitle)

    # אם ההרצה הקודמת נכשלה: מציגים את השגיאה ומאפשרים להמשיך מאותה נקודה
    if ss.error:
        st.error(f"הבדיקה נעצרה בגלל שגיאה:\n\n{ss.error}")
        a, b, _ = st.columns([1, 1, 2])
        if a.button("להמשיך מאותה נקודה", type="primary", width="stretch"):
            ss.error = None
            st.rerun()
        if b.button("חזרה להתחלה", width="stretch"):
            state.reset()
            st.rerun()
        return

    main, side = st.columns([1.35, 1], gap="large")
    with main:
        with st.container(border=True):
            now_ph = st.empty()
            prog_ph = st.empty()
    with side:
        with st.container(border=True):
            st.markdown('<div class="card-title">מה קורה עכשיו</div>', unsafe_allow_html=True)
            log_ph = st.empty()

    values = state.graph_values()
    names = {s["student_id"]: s["name"] for s in values.get("submissions", [])}
    t = {"total": len(values.get("queue") or []), "done": 0, "current": None, "node": None, "log": []}

    def draw():
        name = names.get(t["current"], "")
        label = state.NODE_LABELS.get(t["node"], "מתחילה...")
        initial = c.esc(name[:1]) if name else "⋯"
        who = c.esc(name) if name else "מכינה את הבדיקה"
        now_ph.markdown(
            f'<div class="now"><div class="now-avatar">{initial}</div><div>'
            f'<div class="now-name">{who}</div><div class="now-step pulse">{c.esc(label)}</div></div></div>',
            unsafe_allow_html=True)
        if t["total"]:
            prog_ph.progress(min(t["done"] / t["total"], 1.0),
                             text=f"{t['done']} מתוך {t['total']} עבודות נבדקו")
        else:
            prog_ph.progress(0.0, text="מכינה...")
        rows = "".join(f'<div class="log-row"><span class="log-dot"></span>{c.esc(msg)}'
                       f'<span class="log-time">{tm}</span></div>' for tm, msg in t["log"])
        log_ph.markdown(f'<div class="log">{rows or "<span class=muted>מתחילה...</span>"}</div>',
                        unsafe_allow_html=True)

    def on_event(node, update):
        if "submissions" in update:
            names.update({s["student_id"]: s["name"] for s in update["submissions"]})
        if node in ("load_submissions", "teacher_review") and "queue" in update:
            t["total"], t["done"] = len(update["queue"]), 0
        if node == "pick_next":
            t["current"] = update.get("current_id")
        if node == "save_feedback":
            t["done"] += 1
        t["node"] = node
        msg = state.NODE_LABELS.get(node, node)
        if node in ("grade_student", "self_check", "save_feedback") and names.get(t["current"]):
            msg += f" · {names[t['current']]}"
        if node != "pick_next":
            t["log"].insert(0, (datetime.now().strftime("%H:%M:%S"), msg))
            del t["log"][9:]
        draw()

    draw()
    paused = None
    try:
        paused = state.run_segment(on_event)
    except Exception as e:  # שגיאה (למשל רשת או מפתח) - נשמרת ומוצגת, הגרף ממשיך מה-checkpoint
        ss.error = f"{type(e).__name__}: {e}"
        st.rerun()

    if paused is not None:
        # הגרף עצר לאישור המורה: עותק עבודה של המשובים, שעליו המורה עורכת
        ss.summary = paused
        ss.work = copy.deepcopy(paused["feedbacks"])
        ss.recheck = set()
        ss.editor_version += 1
        ss.stage = "review"
    else:
        ss.stage = "done"
    st.rerun()
