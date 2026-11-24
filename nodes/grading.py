"""
הבדיקה: לולאה חיצונית על התלמידות ולולאה פנימית של בדיקה עצמית.
grade_student ו-self_check = מודל. pick_next ו-save_feedback = קוד.
"""
import re

from llm import get_llm
from prompts import (GRADE_BASIC_HUMAN, GRADE_BASIC_SYSTEM, GRADE_RUBRIC_HUMAN,
                     GRADE_RUBRIC_SYSTEM, RETRY_NOTE, SELF_CHECK_HUMAN, SELF_CHECK_SYSTEM)
from schemas import (NEEDS_REVIEW_FLAG, BasicGradingResult, GradingResult, GradingState,
                     QuestionResult, Rubric, SelfCheckResult, StudentFeedback)

MAX_GRADE_ATTEMPTS = 2


# ---------- פונקציות שמשמשות גם את הגרף וגם את ההערכה ב-LangSmith ----------
def grade_answer(exercise: str, answer: str, student_id: str,
                 rubric: Rubric, retry_reason: str = "") -> GradingResult:
    """בודקת הגשה אחת לפי המחוון: נקודות והערה לכל שאלה. משמשת את האפליקציה ואת ניסוי 2."""
    retry_note = RETRY_NOTE.format(reason=retry_reason) if retry_reason else ""
    human = GRADE_RUBRIC_HUMAN.format(exercise=exercise, rubric=rubric.to_text(),
                                      student_id=student_id, answer=answer, retry_note=retry_note)
    llm = get_llm().with_structured_output(GradingResult)
    return llm.invoke([("system", GRADE_RUBRIC_SYSTEM), ("human", human)])


def grade_answer_basic(exercise: str, answer: str, student_id: str) -> BasicGradingResult:
    """הפרומפט הבסיסי "בדוק ותן ציון", בלי מחוון. משמש רק את ניסוי 1 בהערכה."""
    human = GRADE_BASIC_HUMAN.format(exercise=exercise, student_id=student_id, answer=answer)
    llm = get_llm().with_structured_output(BasicGradingResult)
    return llm.invoke([("system", GRADE_BASIC_SYSTEM), ("human", human)])


def check_grading(exercise: str, rubric: Rubric, answer: str, result: GradingResult) -> SelfCheckResult:
    """המודל בודק את הבדיקה: מבוססת על התשובה, טון ענייני, ציון מתאים למחוון."""
    human = SELF_CHECK_HUMAN.format(exercise=exercise, rubric=rubric.to_text(), answer=answer,
                                    grading=result.model_dump_json(indent=2))
    llm = get_llm().with_structured_output(SelfCheckResult)
    return llm.invoke([("system", SELF_CHECK_SYSTEM), ("human", human)])


def final_question_results(result: GradingResult, rubric: Rubric) -> list[QuestionResult]:
    """קוד בלבד: לכל שאלה - מספר שאלה מנוקה, הנקודות מהמודל + הבונוס של השאלה
    (נקודות שהקריטריונים לא חילקו), ולא יותר מהניקוד המקסימלי של השאלה.
    משמשת גם את הגרף וגם את ההערכה, כדי שהחישוב יהיה זהה."""
    max_by_q = rubric.max_by_question()
    bonus_by_q = rubric.bonus_by_question()
    questions = []
    for q in result.questions:
        key = question_key(q.question)
        points = min(max_by_q.get(key, 100), q.points + bonus_by_q.get(key, 0))
        questions.append(q.model_copy(update={"question": key, "points": points}))
    return questions


def grade_with_self_check(exercise: str, answer: str, student_id: str,
                          rubric: Rubric) -> tuple[GradingResult, bool]:
    """אותה לולאה כמו בגרף (grade_student -> self_check, עד 2 ניסיונות), אבל בלי הגרף.
    משמשת את ההערכה ב-LangSmith. מחזירה (הבדיקה האחרונה, האם הבדיקה העצמית עברה)."""
    reason = ""
    result = None
    for _ in range(MAX_GRADE_ATTEMPTS):
        result = grade_answer(exercise, answer, student_id, rubric, reason)
        check = check_grading(exercise, rubric, answer, result)
        if check.passed:
            return result, True
        reason = check.reason
    return result, False


def question_key(label: str) -> str:
    """מנקה את מספר השאלה שהמודל החזיר, כדי שיתאים למחוון: "Question 1" / "שאלה 1" -> "1"."""
    return re.sub(r"^\s*(question|שאלה)\s*", "", label, flags=re.IGNORECASE).strip()


def _current_submission(state: GradingState):
    # מציאת ההגשה של התלמידה הנוכחית לפי ה-ID
    return next(s for s in state["submissions"] if s["student_id"] == state["current_id"])


# ---------- הצמתים ----------
def pick_next(state: GradingState) -> dict:
    """קוד: לוקח את התלמידה הראשונה בתור ומאפס את מונה הניסיונות."""
    return {
        "current_id": state["queue"][0],
        "attempts": 0,
        "self_check_reason": "",
        "self_check_passed": False,
        "current_result": None,
    }


def grade_student(state: GradingState) -> dict:
    """מודל: בודק את התשובה. בניסיון השני מקבל גם את הסיבה שהבדיקה העצמית נכשלה."""
    sub = _current_submission(state)
    result = grade_answer(state["exercise_description"], sub["text"], sub["student_id"],
                          state["rubric"], state.get("self_check_reason", ""))
    return {"current_result": result, "attempts": state.get("attempts", 0) + 1}


def self_check(state: GradingState) -> dict:
    """מודל: בודק את האובייקט שהוחזר. הקוד רק שומר את התשובה."""
    sub = _current_submission(state)
    check = check_grading(state["exercise_description"], state["rubric"], sub["text"],
                          state["current_result"])
    return {"self_check_passed": check.passed,
            "self_check_reason": "" if check.passed else check.reason}


def save_feedback(state: GradingState) -> dict:
    """קוד: בונה StudentFeedback - מוסיף שם, בונוס ודגל אם צריך, ומוציא את התלמידה מהתור."""
    sub = _current_submission(state)
    result = state["current_result"]
    questions = final_question_results(result, state["rubric"])

    flags = list(result.flags)
    if not state["self_check_passed"]:
        flags.append(NEEDS_REVIEW_FLAG)

    feedback = StudentFeedback(
        student_id=sub["student_id"],
        name=sub["name"],  # השם נוסף כאן, בקוד, אחרי המודל
        # הציון הסופי מחושב בקוד: סכום הנקודות של כל השאלות (כולל הבונוס), עד 100
        score=min(100, sum(q.points for q in questions)),
        question_results=questions,
        comment=result.general_comment,
        flags=flags,
    )
    # בבדיקה חוזרת: מחליפים את המשוב הקודם של אותה תלמידה
    others = [f for f in state.get("feedbacks", []) if f.student_id != feedback.student_id]
    feedbacks = sorted(others + [feedback], key=lambda f: f.student_id)
    return {"feedbacks": feedbacks, "queue": state["queue"][1:]}


# ---------- פונקציות ניתוב (קוד בלבד: מחליטות לאן ממשיכים לפי הפלט) ----------
def route_after_self_check(state: GradingState) -> str:
    # לולאה פנימית: עבר, או שנגמרו הניסיונות -> שומרים. אחרת -> בודקים שוב
    if state["self_check_passed"] or state["attempts"] >= MAX_GRADE_ATTEMPTS:
        return "save_feedback"
    return "grade_student"
