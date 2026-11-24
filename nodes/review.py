"""
אישור המורה - human-in-the-loop.
interrupt עוצר את הגרף ושולח למורה את דף הסיכום.
הגרף ממשיך רק כשהמורה מחזירה תשובה דרך Command(resume=...).
"""
from langgraph.types import interrupt

from schemas import GradingState, TeacherAction


def teacher_review(state: GradingState) -> dict:
    """צומת: מציג למורה את כל הכיתה ומחיל את ההחלטה שלה."""
    # מה שהמורה רואה. אין כאן מי העתיקה ממי, רק מספר הקבוצות והדגלים.
    # עונש ההעתקה כבר מופיע בציון ובהערה, והמורה יכולה לערוך אותם.
    summary = {
        "rubric": state["rubric"].model_dump(),
        "rubric_warning": state.get("rubric_warning", ""),
        "feedbacks": [f.model_dump() for f in state["feedbacks"]],
        "duplicate_groups": state.get("duplicate_groups", 0),
    }
    # כאן הגרף נעצר. כשהמורה עונה, הצומת רץ מההתחלה ו-interrupt מחזיר את התשובה שלה.
    answer = interrupt(summary)
    action = TeacherAction.model_validate(answer)

    # 1. החלת העריכות של המורה (ציון/הערה)
    edited = {f.student_id: f for f in action.edited_feedbacks}
    feedbacks = [edited.get(f.student_id, f) for f in state["feedbacks"]]
    update = {"teacher_action": action, "feedbacks": feedbacks}

    valid_ids = {s["student_id"] for s in state["submissions"]}

    # 2. המחוון השתנה -> בודקים מחדש את כל הכיתה
    if action.rubric is not None and action.rubric != state["rubric"]:
        update["rubric"] = action.rubric
        update["rubric_warning"] = ""
        update["queue"] = [s["student_id"] for s in state["submissions"]]
    # 3. בדיקה חוזרת -> רק התלמידות שנבחרו
    elif action.action == "recheck":
        update["queue"] = [sid for sid in action.recheck_ids if sid in valid_ids]
    # 4. אישור -> הנתונים נשמרים ב-approved_feedbacks. מכאן המודל כבר לא נוגע בהם.
    else:
        update["approved_feedbacks"] = feedbacks
        update["queue"] = []

    return update


def route_after_review(state: GradingState) -> str:
    """קוד: יש מישהי בתור -> חוזרים לבדיקה. אושר -> יצירת דפים. אחרת -> שוב למורה."""
    if state.get("queue"):
        return "pick_next"
    if state["teacher_action"].action == "approve":
        return "generate_pages"
    return "teacher_review"  # למשל בדיקה חוזרת בלי אף ID תקין
