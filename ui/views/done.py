"""מסך 4: דפי המשוב מוכנים – הורדה של הכול (zip), של כל דף בנפרד, ושל טבלת ציונים."""
import csv
import io
import statistics
import zipfile
from pathlib import Path

import streamlit as st

from ui import components as c
from ui import state


def _zip_bytes(files: list[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=p.name)
    return buf.getvalue()


def _grades_csv(feedbacks) -> bytes:
    """טבלת ציונים לגיליון של המורה (נפתחת באקסל עם עברית תקינה)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["שם", "ציון", "דגלים"])
    for fb in feedbacks:
        w.writerow([fb.name, fb.score, ", ".join(fb.flags)])
    return buf.getvalue().encode("utf-8-sig")


def render():
    ss = st.session_state
    approved = state.graph_values().get("approved_feedbacks", [])
    out_dir = Path(ss.output_dir)
    files = sorted(out_dir.glob("*.txt"))
    scores = [fb.score for fb in approved]

    c.hero("דפי המשוב מוכנים", f"נוצרו {len(files)} דפי משוב. אפשר להוריד את כולם יחד או כל אחד בנפרד.",
           success=True)
    if scores:
        c.stats([
            ("דפי משוב", len(files), None, False),
            ("ממוצע הכיתה", f"{statistics.mean(scores):.1f}", None, True),
            ("ציון גבוה", max(scores), None, False),
            ("ציון נמוך", min(scores), None, False),
        ])

    a, b, d, _ = st.columns([1.3, 1.1, 1, 1.4])
    with a:
        st.download_button("⬇  הורדת כל דפי המשוב (zip)", _zip_bytes(files), file_name="feedback.zip",
                           mime="application/zip", type="primary", width="stretch", disabled=not files)
    with b:
        st.download_button("⬇  טבלת ציונים (CSV)", _grades_csv(approved), file_name="grades.csv",
                           mime="text/csv", width="stretch", disabled=not approved)
    with d:
        if st.button("בדיקה חדשה", width="stretch"):
            state.reset()
            st.rerun()
    st.caption(f"הקבצים נשמרו גם בתיקייה: {out_dir}")

    st.markdown('<div class="section-title" style="margin-top:18px">דפי המשוב</div>', unsafe_allow_html=True)
    by_name = {fb.name: fb for fb in approved}
    cols = st.columns(2, gap="medium")
    for i, p in enumerate(files):
        fb = by_name.get(p.stem)
        text = p.read_text(encoding="utf-8-sig")
        with cols[i % 2]:
            with st.container(border=True):
                badge = c.score_badge(fb.score) if fb else ""
                st.markdown(f'<div class="q-head"><span class="q-title">{c.esc(p.stem)}</span>{badge}</div>',
                            unsafe_allow_html=True)
                with st.expander("תצוגה מקדימה"):
                    st.markdown(f'<div style="white-space:pre-wrap;line-height:1.7">{c.esc(text)}</div>',
                                unsafe_allow_html=True)
                st.download_button("הורדה", text.encode("utf-8-sig"), file_name=p.name, mime="text/plain",
                                   key=f"dl_{i}", width="stretch")
