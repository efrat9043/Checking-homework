"""
רכיבי תצוגה שחוזרים בכמה מסכים: כותרת, שלבים, כרטיסי מספרים, תגיות, ציון וגרף.
כל טקסט שמגיע מהמשתמשת עובר html.escape לפני שמוצג כ-HTML.
"""
import html

import altair as alt
import pandas as pd
import streamlit as st

from schemas import DUPLICATE_FLAG, NEEDS_REVIEW_FLAG
from ui.theme import BRAND, LINE, MUTED

STEPS = [("upload", "העלאת עבודות"), ("running", "בדיקה"), ("review", "סיכום ואישור"), ("done", "דפי משוב")]


def esc(text) -> str:
    return html.escape(str(text))


def topbar(stage: str):
    """כותרת עליונה: שם המערכת + השלבים, כשהשלב הנוכחי מודגש."""
    order = [s for s, _ in STEPS]
    current = order.index(stage)
    parts = []
    for i, (key, label) in enumerate(STEPS):
        cls = "active" if i == current else ("done" if i < current else "")
        num = "✓" if i < current else str(i + 1)
        parts.append(f'<div class="step {cls}"><span class="num">{num}</span>{label}</div>')
    steps_html = '<div class="step-sep"></div>'.join(parts)
    st.markdown(
        f"""<div class="topbar">
              <div class="brand"><div class="brand-logo">מ</div>
                <div><div class="brand-name">מחוון</div>
                <div class="brand-sub">בדיקת תרגילים חכמה עם אישור מורה</div></div></div>
              <div class="stepper">{steps_html}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, success: bool = False):
    cls = "hero success" if success else "hero"
    st.markdown(f'<div class="{cls}"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)


def stats(items: list[tuple]):
    """שורת כרטיסי מספרים. כל פריט: (כותרת, ערך, הסבר קטן, מודגש?)."""
    cards = []
    for label, value, hint, accent in items:
        cls = "stat accent" if accent else "stat"
        hint_html = f'<div class="hint">{esc(hint)}</div>' if hint else ""
        cards.append(f'<div class="{cls}"><div class="label">{esc(label)}</div>'
                     f'<div class="value">{esc(value)}</div>{hint_html}</div>')
    st.markdown(f'<div class="stats">{"".join(cards)}</div>', unsafe_allow_html=True)


def flag_chips(flags: list[str]) -> str:
    """תגית לכל דגל. הצבע מלווה תמיד בטקסט, לא מחליף אותו."""
    if not flags:
        return '<span class="chip ok">✓ תקין</span>'
    out = []
    for f in flags:
        if f == DUPLICATE_FLAG:
            out.append(f'<span class="chip bad">⧉ {esc(f)}</span>')
        elif f == NEEDS_REVIEW_FLAG:
            out.append(f'<span class="chip warn">⚑ {esc(f)}</span>')
        else:
            out.append(f'<span class="chip info">ⓘ {esc(f)}</span>')
    return "".join(out)


def score_tone(score: int) -> str:
    return "good" if score >= 85 else ("mid" if score >= 56 else "low")


def score_badge(score: int, max_points: int = 100) -> str:
    return f'<span class="score {score_tone(score)}">{score}<small>/ {max_points}</small></span>'


def score_histogram(scores: list[int]):
    """התפלגות הציונים בכיתה: עמודה לכל טווח של 10 נקודות."""
    labels = [f"{i}–{i + 9}" for i in range(0, 90, 10)] + ["90–100"]
    counts = [0] * 10
    for s in scores:
        counts[min(int(s) // 10, 9)] += 1
    df = pd.DataFrame({"טווח": labels, "תלמידות": counts})
    chart = (
        alt.Chart(df)
        .mark_bar(color=BRAND, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("טווח:N", sort=labels, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("תלמידות:Q", title=None, axis=alt.Axis(tickMinStep=1, format="d")),
            tooltip=[alt.Tooltip("טווח:N", title="טווח ציונים"), alt.Tooltip("תלמידות:Q", title="תלמידות")],
        )
        .properties(height=210)
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#EEF0F5", domainColor=LINE,
                        tickColor=LINE, labelFont="Heebo", labelFontSize=12)
    )
    st.altair_chart(chart, width="stretch")


def file_list(names: list[str]):
    """רשימת הקבצים שהועלו, עם סוג הקובץ."""
    rows = []
    for n in names:
        stem, _, ext = n.rpartition(".")
        stem = stem or ext
        ext = ext if stem != ext else ""
        rows.append(f'<div class="file-row"><span class="file-ext">{esc(ext.upper() or "FILE")}</span>'
                    f'<span class="file-name">{esc(stem)}</span></div>')
    st.markdown("".join(rows), unsafe_allow_html=True)
