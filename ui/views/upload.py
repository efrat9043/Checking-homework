"""מסך 1: תיאור התרגיל והעלאת עבודות התלמידות (קבצים בודדים או zip)."""
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from nodes.loader import read_file_text
from ui import components as c
from ui import files, state

SAMPLE_DIR = state.ROOT / "sample_data_multi"
SAMPLE_EXERCISE = state.ROOT / "exercise_multi.txt"


# ---------- פעולות של כפתורים (callbacks רצים לפני ציור הדף, ולכן מותר להם לשנות ערכי שדות) ----------
def _load_sample():
    st.session_state.exercise_text = SAMPLE_EXERCISE.read_text(encoding="utf-8")
    st.session_state.use_sample = True


def _clear_sample():
    st.session_state.use_sample = False


def _exercise_from_file():
    """טעינת תיאור התרגיל מקובץ txt / docx לתוך תיבת הטקסט."""
    uf = st.session_state.get("exercise_file")
    if not uf:
        return
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / uf.name
        path.write_bytes(uf.getvalue())
        st.session_state.exercise_text = read_file_text(path)


def _start(uploads):
    """שומר את הקבצים, יוצר גרף חדש ומעביר למסך הבדיקה."""
    ss = st.session_state
    exercise = ss.exercise_text.strip()
    if not exercise:
        st.error("חסר תיאור תרגיל.")
        return
    if not ss.use_sample and not uploads:
        st.error("לא הועלו קבצים.")
        return

    run_dir = state.new_run_dir()
    names = files.copy_folder(SAMPLE_DIR, run_dir) if ss.use_sample else files.save_uploads(uploads, run_dir)
    if not names:
        st.error("לא נמצאו קבצים מתאימים (גם לא בתוך ה-zip).")
        return

    ss.run_dir = str(run_dir.parent)
    # שם תלמידה -> הקובץ המקורי (להצגה בדף התלמידה). אותו כלל כמו ב-loader.
    ss.file_map = {Path(n).stem.replace("_", " ").strip(): str(run_dir / n) for n in names}
    ss.output_dir = str(state.ROOT / "output" / datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    state.start_graph({"exercise_description": exercise, "input_dir": str(run_dir), "output_dir": ss.output_dir})
    st.rerun()


def render():
    ss = st.session_state
    ss.setdefault("exercise_text", "")
    ss.setdefault("use_sample", False)

    c.hero("בדיקת עבודות לכל הכיתה, בכמה דקות",
           "מעלים את התרגיל ואת עבודות התלמידות. המערכת בונה מחוון, בודקת כל עבודה – ואת מאשרת לפני שנוצר משוב.")

    right, left = st.columns([1.15, 1], gap="large")  # בכיוון ימין-לשמאל העמודה הראשונה מופיעה מימין

    with right:
        with st.container(border=True):
            st.markdown('<div class="card-title">1 · תיאור התרגיל</div>'
                        '<div class="card-sub">אפשר לכתוב ניקוד לכל שאלה, למשל "שאלה 1 (30 נק\')". '
                        'אם לא כתוב – המערכת תחלק את 100 הנקודות לפי האורך והקושי.</div>', unsafe_allow_html=True)
            st.text_area("תיאור התרגיל", key="exercise_text", height=270, label_visibility="collapsed",
                         placeholder="למשל: שאלה 1 – הסבירי מה ההבדל בין list ל-tuple...\nשאלה 2 – כתבי פונקציה...")
            st.file_uploader("או טעינת התרגיל מקובץ (txt / docx)", type=["txt", "docx", "md"],
                             key="exercise_file", on_change=_exercise_from_file)

    uploads = None
    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">2 · עבודות התלמידות</div>'
                        '<div class="card-sub">שם הקובץ (בלי הסיומת) הוא שם התלמידה. '
                        'קבצי קוד, Word, טקסט – או zip אחד עם כולם.</div>', unsafe_allow_html=True)
            if ss.use_sample:
                st.info("נטענה כיתה לדוגמה: 5 עבודות על דף תרגילים עם 3 שאלות.", icon="🧪")
                c.file_list([p.name for p in sorted(SAMPLE_DIR.iterdir()) if p.is_file()])
                st.button("ביטול הדוגמה", on_click=_clear_sample)
            else:
                uploads = st.file_uploader("קבצי התלמידות", accept_multiple_files=True, key="uploads",
                                           label_visibility="collapsed")
                if uploads:
                    st.markdown(f'<div class="muted" style="margin:6px 0">{len(uploads)} קבצים נבחרו</div>',
                                unsafe_allow_html=True)
                    c.file_list([u.name for u in uploads])

    st.markdown(
        """<div class="stats" style="margin-top:18px">
             <div class="stat"><div class="label">🔒 פרטיות</div><div class="hint" style="font-size:14px;color:#1E2235">
               שמות התלמידות מוחלפים במזהה לפני השליחה למודל.</div></div>
             <div class="stat"><div class="label">🧭 מחוון שקוף</div><div class="hint" style="font-size:14px;color:#1E2235">
               ניקוד לכל שאלה וקריטריון – ואפשר לערוך אותו.</div></div>
             <div class="stat"><div class="label">⧉ קבצים זהים</div><div class="hint" style="font-size:14px;color:#1E2235">
               זיהוי אוטומטי של עבודות זהות, בלי לקבוע מי העתיקה ממי.</div></div>
             <div class="stat"><div class="label">👩‍🏫 ההחלטה שלך</div><div class="hint" style="font-size:14px;color:#1E2235">
               שום משוב לא נוצר לפני שאישרת.</div></div>
           </div>""",
        unsafe_allow_html=True,
    )

    b1, b2, _ = st.columns([1.3, 1, 2.2])
    with b1:
        if st.button("התחלת הבדיקה  ←", type="primary", width="stretch"):
            _start(uploads)
    with b2:
        if not ss.use_sample:
            st.button("נסי עם כיתה לדוגמה", on_click=_load_sample, width="stretch")
