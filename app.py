"""
ממשק המורה (Streamlit) – נקודת הכניסה.
הפעלה: לחיצה כפולה על "הפעלת המערכת.bat", או:
    .venv\\Scripts\\python.exe -m streamlit run app.py
כל קוד הממשק נמצא בתיקייה ui/. הגרף והצמתים לא תלויים בממשק.
"""
import streamlit as st

# חייב להיות הקריאה הראשונה ל-Streamlit
st.set_page_config(page_title="מחוון · בדיקת תרגילים", page_icon="📝", layout="wide",
                   initial_sidebar_state="collapsed")

from ui import components as c  # noqa: E402
from ui import state, theme  # noqa: E402
from ui.views import done, review, running, upload  # noqa: E402

theme.inject()
state.init()
c.topbar(st.session_state.stage)

SCREENS = {"upload": upload.render, "running": running.render, "review": review.render, "done": done.render}
SCREENS[st.session_state.stage]()
