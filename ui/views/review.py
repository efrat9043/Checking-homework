"""
מסך 3: דף הסיכום של הכיתה (human-in-the-loop).
המורה רואה את כל הכיתה, עורכת ציונים והערות, מסמנת לבדיקה חוזרת, עורכת את המחוון – ומאשרת.
כל ההחלטות נשלחות לגרף דרך Command(resume=...), בדיוק כמו ב-run_cli.py.
"""
import copy
import statistics
from pathlib import Path

import pandas as pd
import streamlit as st
from langgraph.types import Command

from nodes.loader import read_file_text
from schemas import DUPLICATE_FLAG, Rubric
from ui import components as c
from ui import state

LOW_SCORE = 56  # לתצוגה ולסינון בלבד ("ציון נמוך"), לא משפיע על הבדיקה
CODE_LANGS = {".py": "python", ".java": "java", ".js": "javascript", ".ts": "typescript", ".cpp": "cpp",
              ".c": "c", ".cs": "csharp", ".html": "html", ".sql": "sql"}


def _send(payload: dict, kind: str):
    """שולח את ההחלטה של המורה לגרף וממשיך להרצה."""
    payload["edited_feedbacks"] = copy.deepcopy(st.session_state.work)
    state.go_running(Command(resume=payload), kind)


# ---------------------------------------------------------------- לשונית: הכיתה
def _class_tab(work, by_id, max_by_q):
    ss = st.session_state
    scores = [f["score"] for f in work]

    right, left = st.columns([1, 1.5], gap="large")
    with right:
        with st.container(border=True):
            st.markdown('<div class="card-title">התפלגות ציונים</div>', unsafe_allow_html=True)
            c.score_histogram(scores)
    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">דורשות תשומת לב</div>', unsafe_allow_html=True)
            flagged = [f for f in work if f["flags"]]
            if not flagged:
                st.markdown('<div class="muted">אין עבודות עם דגלים. 🎉</div>', unsafe_allow_html=True)
            for f in flagged:
                st.markdown(f'<div class="file-row"><span class="file-name">{c.esc(f["name"])}</span>'
                            f'<span style="margin-inline-start:auto">{c.flag_chips(f["flags"])}</span></div>',
                            unsafe_allow_html=True)

    st.markdown('<div class="section-title">כל הכיתה</div>', unsafe_allow_html=True)
    f1, f2 = st.columns([1.2, 2])
    with f1:
        search = st.text_input("חיפוש", placeholder="חיפוש לפי שם...", label_visibility="collapsed")
    with f2:
        view = st.segmented_control("סינון", ["הכול", "עם דגלים", f"מתחת ל-{LOW_SCORE}", "סומנו לבדיקה חוזרת"],
                                    default="הכול", label_visibility="collapsed") or "הכול"

    rows = [f for f in work if search.strip() in f["name"]]
    if view == "עם דגלים":
        rows = [f for f in rows if f["flags"]]
    elif view.startswith("מתחת"):
        rows = [f for f in rows if f["score"] < LOW_SCORE]
    elif view == "סומנו לבדיקה חוזרת":
        rows = [f for f in rows if f["student_id"] in ss.recheck]
    if not rows:
        st.info("אין תלמידות שמתאימות לסינון.")
        return

    df = pd.DataFrame([{
        "ID": f["student_id"],
        "שם": f["name"],
        "ציון": f["score"],
        "פירוט שאלות": "  ·  ".join(f"ש{q['question']}: {q['points']}/{max_by_q.get(q['question'], '?')}"
                                    for q in f["question_results"]),
        "דגלים": ", ".join(f["flags"]) or "—",
        "הערה כללית": f["comment"],
        "בדיקה חוזרת": f["student_id"] in ss.recheck,
    } for f in rows])

    # המפתח משתנה כשמשנים סינון או שומרים עריכה בדף התלמידה - כדי שהטבלה תתחיל מהנתונים העדכניים
    edited = st.data_editor(
        df,
        key=f"class_editor_{ss.editor_version}_{view}_{search}",
        hide_index=True,
        width="stretch",
        height=min(42 + 36 * len(df), 600),
        disabled=["ID", "שם", "פירוט שאלות", "דגלים"],
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small"),
            "שם": st.column_config.TextColumn("שם", width="medium"),
            "ציון": st.column_config.NumberColumn("ציון ✎", min_value=0, max_value=100, step=1, format="%d",
                                                  width="small"),
            "פירוט שאלות": st.column_config.TextColumn("פירוט שאלות", width="medium"),
            "דגלים": st.column_config.TextColumn("דגלים", width="medium"),
            "הערה כללית": st.column_config.TextColumn("הערה כללית ✎", width="large"),
            "בדיקה חוזרת": st.column_config.CheckboxColumn("בדיקה חוזרת", width="small"),
        },
    )
    # שמירת העריכות לעותק העבודה
    for _, row in edited.iterrows():
        f = by_id[row["ID"]]
        if not pd.isna(row["ציון"]):
            f["score"] = int(row["ציון"])
        f["comment"] = "" if pd.isna(row["הערה כללית"]) else str(row["הערה כללית"])
        (ss.recheck.add if row["בדיקה חוזרת"] else ss.recheck.discard)(row["ID"])
    st.caption("✎ = אפשר לערוך ישירות בטבלה. עריכה מפורטת לכל שאלה – בלשונית \"תלמידה\".")


# ---------------------------------------------------------------- לשונית: תלמידה
def _student_tab(work, by_id, max_by_q):
    ss = st.session_state
    sid = st.selectbox("בחירת תלמידה", [f["student_id"] for f in work], key="student_pick",
                       format_func=lambda s: f"{by_id[s]['name']}   ·   ציון {by_id[s]['score']}")
    f = by_id[sid]
    ver = ss.editor_version

    right, left = st.columns([1.05, 1], gap="large")
    with right:
        with st.container(border=True):
            st.markdown(f'<div class="q-head"><div class="now-name">{c.esc(f["name"])}</div>'
                        f'{c.score_badge(f["score"])}</div><div>{c.flag_chips(f["flags"])}</div>',
                        unsafe_allow_html=True)
            with st.form(key=f"form_{sid}_{ver}", border=False):
                new_q = []
                for i, q in enumerate(f["question_results"]):
                    mx = max_by_q.get(q["question"], 100)
                    st.markdown(f'<div class="q-head" style="margin-top:14px"><span class="q-title">שאלה {c.esc(q["question"])}'
                                f'</span><span class="q-points">מתוך {mx}</span></div>', unsafe_allow_html=True)
                    pts = st.number_input("נקודות", 0, mx, min(int(q["points"]), mx), key=f"p_{sid}_{ver}_{i}")
                    com = st.text_area("הערה לשאלה", q["comment"], key=f"c_{sid}_{ver}_{i}", height=78)
                    new_q.append((pts, com))
                st.divider()
                total_q = sum(p for p, _ in new_q)
                score = st.number_input("ציון סופי", 0, 100, int(f["score"]), key=f"s_{sid}_{ver}",
                                        help=f"סכום הנקודות בשאלות כרגע: {total_q}. "
                                             "הציון הסופי כולל בונוס / הורדה, ולכן יכול להיות שונה.")
                general = st.text_area("הערה כללית", f["comment"], key=f"g_{sid}_{ver}", height=70)
                recheck = st.checkbox("לסמן לבדיקה חוזרת", value=sid in ss.recheck, key=f"r_{sid}_{ver}")
                if st.form_submit_button("שמירת השינויים", type="primary", width="stretch"):
                    for q, (pts, com) in zip(f["question_results"], new_q):
                        q["points"], q["comment"] = int(pts), com
                    f["score"], f["comment"] = int(score), general
                    (ss.recheck.add if recheck else ss.recheck.discard)(sid)
                    ss.editor_version += 1
                    st.toast(f"השינויים של {f['name']} נשמרו", icon="✅")
                    st.rerun()

    with left:
        with st.container(border=True):
            path = ss.file_map.get(f["name"])
            st.markdown(f'<div class="card-title">העבודה שהוגשה</div>'
                        f'<div class="card-sub">{c.esc(Path(path).name) if path else ""}</div>',
                        unsafe_allow_html=True)
            text = read_file_text(Path(path)) if path and Path(path).exists() else ""
            if text.strip():
                st.code(text, language=CODE_LANGS.get(Path(path).suffix.lower()))
            else:
                st.markdown('<div class="muted">הקובץ ריק.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- לשונית: מחוון
def _rubric_rows(rubric: dict) -> pd.DataFrame:
    return pd.DataFrame([{"שאלה": q["number"], "ניקוד שאלה": q["max_points"], "קריטריון": cr["name"],
                          "תיאור": cr["description"], "ניקוד קריטריון": cr["max_points"]}
                         for q in rubric["questions"] for cr in q["criteria"]])


def _rows_to_rubric(df: pd.DataFrame):
    """בונה מחוון מהטבלה הערוכה. מחזיר (Rubric, הודעת שגיאה)."""
    questions, order = {}, []
    for _, r in df.dropna(how="all").iterrows():
        num = str(r["שאלה"]).strip()
        if not num or num == "nan" or pd.isna(r["ניקוד קריטריון"]):
            return None, "בכל שורה צריך מספר שאלה וניקוד קריטריון."
        if num not in questions:
            order.append(num)
            questions[num] = {"number": num, "max_points": None, "criteria": []}
        if questions[num]["max_points"] is None and not pd.isna(r["ניקוד שאלה"]):
            questions[num]["max_points"] = int(r["ניקוד שאלה"])
        questions[num]["criteria"].append({"name": str(r["קריטריון"] or ""), "description": str(r["תיאור"] or ""),
                                           "max_points": int(r["ניקוד קריטריון"])})
    for q in questions.values():
        if q["max_points"] is None:
            return None, f"חסר ניקוד לשאלה {q['number']}."
    try:
        return Rubric.model_validate({"questions": [questions[n] for n in order]}), None
    except Exception as e:  # למשל ניקוד מחוץ לטווח
        return None, f"המחוון לא תקין: {e}"


def _rubric_tab(rubric: dict):
    ss = st.session_state
    right, left = st.columns([1, 1.25], gap="large")
    with right:
        for q in rubric["questions"]:
            with st.container(border=True):
                crit = "".join(
                    f'<div class="crit"><span class="crit-name">{c.esc(cr["name"])}</span> '
                    f'<span class="crit-pts">· {cr["max_points"]} נק\'</span>'
                    f'<div class="crit-desc">{c.esc(cr["description"])}</div></div>' for cr in q["criteria"])
                st.markdown(f'<div class="q-head"><span class="q-title">שאלה {c.esc(q["number"])}</span>'
                            f'<span class="q-points">{q["max_points"]} נקודות</span></div>{crit}',
                            unsafe_allow_html=True)
    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">עריכת המחוון</div><div class="card-sub">'
                        'שינוי במחוון יבדוק מחדש את כל הכיתה. עריכות ידניות בציונים יוחלפו בבדיקה החדשה.</div>',
                        unsafe_allow_html=True)
            edited = st.data_editor(_rubric_rows(rubric), key=f"rubric_editor_{ss.editor_version}",
                                    num_rows="dynamic", hide_index=True, width="stretch",
                                    column_config={
                                        "שאלה": st.column_config.TextColumn("שאלה", width="small"),
                                        "ניקוד שאלה": st.column_config.NumberColumn("ניקוד שאלה", min_value=1,
                                                                                    max_value=100, step=1),
                                        "קריטריון": st.column_config.TextColumn("קריטריון", width="medium"),
                                        "תיאור": st.column_config.TextColumn("תיאור", width="large"),
                                        "ניקוד קריטריון": st.column_config.NumberColumn("ניקוד קריטריון",
                                                                                        min_value=1, max_value=100,
                                                                                        step=1),
                                    })
            new_rubric, error = _rows_to_rubric(edited)
            changed = new_rubric is not None and new_rubric.model_dump() != Rubric.model_validate(rubric).model_dump()
            if error:
                st.error(error)
            elif changed:
                for p in new_rubric.problems():
                    st.warning(p)
                if new_rubric.is_valid():
                    st.success("המחוון החדש תקין.")
            if st.button("שמירת המחוון ובדיקה מחדש של כל הכיתה", type="primary", disabled=not changed,
                         width="stretch"):
                _send({"action": "recheck", "rubric": new_rubric.model_dump()}, "regrade")
                st.rerun()


# ---------------------------------------------------------------- אישור
@st.dialog("אישור סופי")
def _confirm_dialog():
    ss = st.session_state
    st.write(f"ייווצרו **{len(ss.work)} דפי משוב** לפי הציונים וההערות שבטבלה. "
             "אחרי האישור המודל כבר לא משנה את הנתונים.")
    if ss.recheck:
        st.warning(f"{len(ss.recheck)} תלמידות סומנו לבדיקה חוזרת. אישור עכשיו יתעלם מהסימון.")
    a, b = st.columns(2)
    if a.button("כן, ליצור את דפי המשוב", type="primary", width="stretch"):
        _send({"action": "approve"}, "finalize")
        st.rerun()
    if b.button("ביטול", width="stretch"):
        st.rerun()


def _action_bar(by_id):
    ss = st.session_state
    st.markdown('<div class="section-title" style="margin-top:22px">ההחלטה שלך</div>', unsafe_allow_html=True)
    with st.container(border=True):
        text, b1, b2 = st.columns([2.2, 1.2, 1.3], vertical_alignment="center")
        with text:
            marked = ", ".join(by_id[s]["name"] for s in sorted(ss.recheck))
            st.markdown('<div class="card-sub">העריכות שלך נשמרות. כשהכול נראה טוב – מאשרים, ונוצר דף משוב לכל תלמידה.'
                        + (f'<br><b>לבדיקה חוזרת:</b> {c.esc(marked)}' if marked else "") + '</div>',
                        unsafe_allow_html=True)
        with b1:
            if st.button(f"בדיקה חוזרת ({len(ss.recheck)})", disabled=not ss.recheck, width="stretch"):
                _send({"action": "recheck", "recheck_ids": sorted(ss.recheck)}, "recheck")
                st.rerun()
        with b2:
            if st.button("אישור ויצירת דפי משוב", type="primary", width="stretch"):
                _confirm_dialog()


# ---------------------------------------------------------------- המסך
def render():
    ss = st.session_state
    summary, work = ss.summary, ss.work
    rubric = summary["rubric"]
    by_id = {f["student_id"]: f for f in work}
    max_by_q = {q["number"]: q["max_points"] for q in rubric["questions"]}
    scores = [f["score"] for f in work]

    c.hero("דף הסיכום של הכיתה", "בדקי, ערכי במידת הצורך ואשרי. רק אחרי האישור נוצרים דפי המשוב.")
    c.stats([
        ("תלמידות", len(work), f"{len(rubric['questions'])} שאלות בדף", False),
        ("ממוצע הכיתה", f"{statistics.mean(scores):.1f}", f"חציון {statistics.median(scores):g}", True),
        ("טווח ציונים", f"{min(scores)}–{max(scores)}", None, False),
        ("דורשות תשומת לב", sum(1 for f in work if f["flags"]), "עם דגל אחד לפחות", False),
    ])

    if summary.get("rubric_warning"):
        st.warning(summary["rubric_warning"], icon="⚠️")
    if summary.get("duplicate_groups"):
        dup = ", ".join(f["name"] for f in work if DUPLICATE_FLAG in f["flags"])
        st.warning(f"זוהו {summary['duplicate_groups']} קבוצות של קבצים זהים. תלמידות מסומנות: {dup}. "
                   "לכל אחת הורדו 70% מהציון – אפשר לשנות לפני האישור.", icon="📑")

    tab_class, tab_student, tab_rubric = st.tabs(["📋  הכיתה", "🔍  תלמידה", "🧭  מחוון"])
    with tab_class:
        _class_tab(work, by_id, max_by_q)
    with tab_student:
        _student_tab(work, by_id, max_by_q)
    with tab_rubric:
        _rubric_tab(rubric)

    _action_bar(by_id)
