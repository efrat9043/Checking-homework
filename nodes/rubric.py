"""
יצירת מחוון - המודל מחליט על הקריטריונים והנקודות, מתוך תיאור התרגיל בלבד.
הקוד רק בודק את הסכומים (חשבון, לא שיפוט): השאלות = 100, ובכל שאלה הקריטריונים בין 90% ל-100% מהניקוד שלה.
"""
from llm import get_llm
from prompts import RUBRIC_HUMAN, RUBRIC_SYSTEM
from schemas import GradingState, Rubric

MAX_RUBRIC_ATTEMPTS = 2


def generate_rubric(exercise: str) -> tuple[Rubric, str]:
    """מחזירה (מחוון, אזהרה). אזהרה ריקה = המחוון תקין. משמשת גם את ההערכה."""
    llm = get_llm().with_structured_output(Rubric)
    messages = [("system", RUBRIC_SYSTEM), ("human", RUBRIC_HUMAN.format(exercise=exercise))]

    rubric = None
    for _ in range(MAX_RUBRIC_ATTEMPTS):
        rubric = llm.invoke(messages)
        if rubric.is_valid():
            return rubric, ""

    warning = "המחוון לא תקין: " + "; ".join(rubric.problems()) + ". יש לתקן את המחוון."
    return rubric, warning


def create_rubric(state: GradingState) -> dict:
    """צומת: יוצר מחוון ושומר אזהרה אם הוא לא תקין."""
    rubric, warning = generate_rubric(state["exercise_description"])
    return {"rubric": rubric, "rubric_warning": warning}
