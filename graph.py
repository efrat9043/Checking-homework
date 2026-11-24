"""
בניית הגרף: חיבור כל הצמתים והקשתות.
דרישות התרגיל שמתקיימות כאן:
- langgraph (StateGraph)
- לולאות: בדיקה עצמית (self_check -> grade_student), ומעבר על כל התלמידות (save_feedback -> pick_next)
- ענף מותנה: detect_duplicates רק אם יש קבצים זהים
- interrupt: teacher_review, עם MemorySaver ששומר את המצב בזמן ההמתנה למורה
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from nodes.duplicates import detect_duplicates, find_duplicate_groups
from nodes.grading import (grade_student, pick_next, route_after_self_check,
                           save_feedback, self_check)
from nodes.loader import load_submissions
from nodes.output import generate_pages
from nodes.review import route_after_review, teacher_review
from nodes.rubric import create_rubric
from schemas import GradingState

# כל תלמידה עוברת 4-6 צעדים, וברירת המחדל של langgraph היא 25 צעדים בלבד
RECURSION_LIMIT = 1000


def route_after_save(state: GradingState) -> str:
    """לולאה חיצונית + ענף מותנה."""
    if state["queue"]:
        return "pick_next"  # יש עוד תלמידות
    if find_duplicate_groups(state["submissions"]):
        return "detect_duplicates"  # ענף מותנה: יש קבצים זהים
    return "teacher_review"


def build_graph(checkpointer=None):
    g = StateGraph(GradingState)

    g.add_node("load_submissions", load_submissions)
    g.add_node("create_rubric", create_rubric)
    g.add_node("pick_next", pick_next)
    g.add_node("grade_student", grade_student)
    g.add_node("self_check", self_check)
    g.add_node("save_feedback", save_feedback)
    g.add_node("detect_duplicates", detect_duplicates)
    g.add_node("teacher_review", teacher_review)
    g.add_node("generate_pages", generate_pages)

    # קשתות קבועות
    g.add_edge(START, "load_submissions")
    g.add_edge("load_submissions", "create_rubric")
    g.add_edge("create_rubric", "pick_next")
    g.add_edge("pick_next", "grade_student")
    g.add_edge("grade_student", "self_check")
    g.add_edge("detect_duplicates", "teacher_review")
    g.add_edge("generate_pages", END)

    # קשתות מותנות: הקוד בוחר לאן ממשיכים לפי מה שבמצב
    g.add_conditional_edges("self_check", route_after_self_check, ["grade_student", "save_feedback"])
    g.add_conditional_edges("save_feedback", route_after_save,
                            ["pick_next", "detect_duplicates", "teacher_review"])
    g.add_conditional_edges("teacher_review", route_after_review,
                            ["pick_next", "generate_pages", "teacher_review"])

    # MemorySaver שומר את המצב בזיכרון, כדי שאפשר יהיה להמשיך אחרי ה-interrupt
    return g.compile(checkpointer=checkpointer or MemorySaver())
