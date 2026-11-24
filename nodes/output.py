"""
יצירת דפי המשוב - קוד בלבד, בלי מודל.
קובץ טקסט קצר לכל תלמידה: שם, ציון סופי, ולכל שאלה נקודות והערה.
הפורמט מוגדר בפונקציה אחת (format_feedback), כך שקל להחליף אותו בעתיד.
"""
from pathlib import Path

from schemas import GradingState, Rubric, StudentFeedback

OUTPUT_DIR = Path("output")


def format_feedback(fb: StudentFeedback, rubric: Rubric) -> str:
    """בונה את תוכן הקובץ לתלמידה אחת. דגלים לא נכללים - הם מיועדים למורה."""
    max_by_q = rubric.max_by_question()
    lines = [f"שם: {fb.name}", f"ציון: {fb.score}", ""]
    for q in fb.question_results:
        max_points = max_by_q.get(q.question)
        points = f"{q.points}/{max_points}" if max_points else f"{q.points}"
        lines.append(f"שאלה {q.question} ({points}):")
        lines.append(q.comment.strip())
        lines.append("")
    if fb.comment.strip():  # הערה כללית, למשל משפט ההעתקה
        lines.append(fb.comment.strip())
    return "\n".join(lines).rstrip() + "\n"


def generate_pages(state: GradingState) -> dict:
    """צומת: קובץ אחד לכל תלמידה, רק מתוך approved_feedbacks."""
    # אם הוגדרה תיקייה לריצה הזו (בממשק) - שומרים שם; אחרת בתיקייה הרגילה output/
    out_dir = Path(state.get("output_dir") or OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    for fb in state["approved_feedbacks"]:
        path = out_dir / f"{fb.name}.txt"
        # utf-8-sig: כדי שגם Notepad ישן יציג את העברית נכון
        path.write_text(format_feedback(fb, state["rubric"]), encoding="utf-8-sig")
    return {}
