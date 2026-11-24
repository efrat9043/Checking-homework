"""
ניהול המצב של הממשק בין לחיצות (st.session_state) והרצת הגרף.
המסכים: upload -> running -> review -> (running -> review)* -> done
הגרף נשמר ב-session_state יחד עם thread_id, וה-MemorySaver שבו זוכר איפה הגרף עצר (interrupt).
"""
import shutil
import tempfile
import uuid
from pathlib import Path

import streamlit as st

from graph import RECURSION_LIMIT, build_graph

ROOT = Path(__file__).resolve().parent.parent

# תיאור כל צומת בעברית, ליומן ההתקדמות
NODE_LABELS = {
    "load_submissions": "קריאת הקבצים והסתרת שמות התלמידות",
    "create_rubric": "בניית מחוון מתיאור התרגיל",
    "pick_next": "מעבר לתלמידה הבאה",
    "grade_student": "בדיקת התשובה לפי המחוון",
    "self_check": "בדיקה עצמית של הבדיקה",
    "save_feedback": "שמירת המשוב",
    "detect_duplicates": "איתור קבצים זהים",
    "teacher_review": "הכנת דף הסיכום",
    "generate_pages": "יצירת דפי המשוב",
}

DEFAULTS = {
    "stage": "upload",        # המסך הנוכחי
    "graph": None,            # הגרף המקומפל (עם MemorySaver)
    "config": None,           # thread_id + recursion_limit
    "pending": None,          # הקלט הבא לגרף (מילון התחלה או Command(resume=...))
    "segment_started": False, # האם כבר התחלנו להריץ את המקטע הנוכחי (להמשך אחרי רענון)
    "run_kind": "initial",    # initial / recheck / regrade / finalize
    "summary": None,          # מה שה-interrupt שלח: מחוון + כל המשובים
    "work": None,             # עותק עבודה של המשובים, עם העריכות של המורה
    "recheck": set(),         # student_id שסומנו לבדיקה חוזרת
    "editor_version": 0,      # משתנה כשנשמרות עריכות, כדי לרענן את טבלת העריכה
    "run_dir": None,          # תיקייה זמנית עם קבצי ההגשות
    "output_dir": None,       # לאן נשמרים דפי המשוב
    "file_map": {},           # שם תלמידה -> נתיב הקובץ המקורי
    "error": None,            # שגיאה אחרונה בהרצה
}


def init():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (set, dict)) else value


def reset():
    """בדיקה חדשה: מוחקים את תיקיית ההגשות הזמנית ומאפסים את המצב."""
    run_dir = st.session_state.get("run_dir")
    if run_dir:
        shutil.rmtree(run_dir, ignore_errors=True)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init()


def new_run_dir() -> Path:
    """תיקייה זמנית לקבצים של הריצה הזו (מחוץ לפרויקט)."""
    return Path(tempfile.mkdtemp(prefix="grading_")) / "submissions"


def start_graph(graph_input: dict):
    """יוצר גרף חדש ו-thread חדש, ומעביר למסך ההתקדמות."""
    ss = st.session_state
    ss.graph = build_graph()
    ss.config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": RECURSION_LIMIT}
    go_running(graph_input, "initial")


def go_running(graph_input, kind: str):
    ss = st.session_state
    ss.pending = graph_input
    ss.segment_started = False
    ss.run_kind = kind
    ss.error = None
    ss.stage = "running"


def graph_values() -> dict:
    """המצב הנוכחי של הגרף (submissions, rubric, approved_feedbacks...)."""
    ss = st.session_state
    return ss.graph.get_state(ss.config).values if ss.graph else {}


def run_segment(on_event):
    """
    מריץ את הגרף עד שהוא עוצר (interrupt) או מסתיים.
    אם Streamlit רענן את הדף באמצע ריצה - ממשיכים מה-checkpoint האחרון (קלט None) ולא מתחילים מחדש.
    מחזיר את מה שה-interrupt שלח, או None אם הגרף הסתיים.
    """
    ss = st.session_state
    graph_input = None if ss.segment_started else ss.pending
    ss.segment_started = True
    paused = None
    for chunk in ss.graph.stream(graph_input, ss.config, stream_mode="updates"):
        for node, update in chunk.items():
            if node == "__interrupt__":
                paused = update[0].value
                continue
            on_event(node, update or {})
    ss.segment_started = False
    return paused
