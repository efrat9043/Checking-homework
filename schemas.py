"""
המבנים (סכמות) של הפרויקט.
כל מה שהמודל מחזיר מוגדר כאן כמחלקת Pydantic, ו-with_structured_output
מכריח את המודל להחזיר אובייקט בדיוק במבנה הזה.
תרגיל יכול להכיל שאלה אחת או כמה שאלות. תרגיל עם שאלה אחת = דף עם שאלה מספר 1.
"""
from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field

# ---------- דגלים ----------
# דגלים שהמודל רשאי לסמן (החלטת תוכן = החלטה של המודל). מתייחסים להגשה כולה.
MODEL_FLAGS = Literal["לא הוגש", "לא רלוונטי", "לא ניתן לבדיקה"]
# דגל שרק הקוד מסמן (השוואה דטרמיניסטית). המודל לא מכיר אותו בכלל.
DUPLICATE_FLAG = "קובץ זהה לקובץ אחר"
# דגל שהקוד מוסיף כשהבדיקה העצמית נכשלה גם בניסיון השני
NEEDS_REVIEW_FLAG = "נדרשת בדיקת מורה"


# ---------- מחוון ----------
class Criterion(BaseModel):
    """קריטריון אחד בתוך שאלה."""
    name: str = Field(description="Short name of the criterion")
    description: str = Field(description="What a full-credit answer must show for this criterion, and what loses points")
    max_points: int = Field(ge=1, le=100, description="Maximum points for this criterion")


MIN_CRITERIA_SHARE = 0.9  # הקריטריונים בשאלה חייבים לחלק לפחות 90% מניקוד השאלה


class Question(BaseModel):
    """שאלה אחת במחוון: מספר, ניקוד מקסימלי וקריטריונים."""
    number: str = Field(description="Question number as written in the exercise, e.g. '1', '2', '3a'")
    max_points: int = Field(ge=1, le=100, description="Maximum points for this question")
    criteria: list[Criterion] = Field(description="1-4 criteria whose max_points sum to this question's max_points")

    def criteria_total(self) -> int:
        # כמה נקודות הקריטריונים מחלקים בפועל
        return sum(c.max_points for c in self.criteria)

    def is_valid(self) -> bool:
        # תקין אם הקריטריונים מחלקים בין 90% ל-100% מניקוד השאלה (למשל שאלה של 20: בין 18 ל-20)
        return self.max_points * MIN_CRITERIA_SHARE <= self.criteria_total() <= self.max_points

    def bonus_points(self) -> int:
        # הנקודות שהקריטריונים לא חילקו ניתנות לכל תלמידה בשאלה הזו (שאלה של 20, חולקו 18 -> בונוס 2)
        return max(0, self.max_points - self.criteria_total())


class Rubric(BaseModel):
    """המחוון כולו: רשימת שאלות. סכום הנקודות של כל השאלות חייב להיות בדיוק 100."""
    questions: list[Question] = Field(description="One entry per question in the exercise. The questions' max_points sum to exactly 100")

    def total_points(self) -> int:
        # חישוב פשוט (לא שיפוט): סכום הנקודות של כל השאלות
        return sum(q.max_points for q in self.questions)

    def is_valid(self) -> bool:
        # תקין אם השאלות מסתכמות בדיוק ב-100, וכל שאלה תקינה בפני עצמה
        return self.total_points() == 100 and all(q.is_valid() for q in self.questions)

    def problems(self) -> list[str]:
        # תיאור הבעיות במחוון לא תקין (לאזהרה למורה)
        found = []
        if self.total_points() != 100:
            found.append(f"סכום השאלות הוא {self.total_points()} ולא 100")
        for q in self.questions:
            if not q.is_valid():
                found.append(f"בשאלה {q.number} ({q.max_points} נק') הקריטריונים מחלקים {q.criteria_total()} נק'")
        return found

    def max_by_question(self) -> dict[str, int]:
        # מספר שאלה -> ניקוד מקסימלי (לתצוגה בדף התלמידה)
        return {q.number: q.max_points for q in self.questions}

    def bonus_by_question(self) -> dict[str, int]:
        # מספר שאלה -> בונוס (הנקודות שהקריטריונים לא חילקו)
        return {q.number: q.bonus_points() for q in self.questions}

    def to_text(self) -> str:
        # הפיכת המחוון לטקסט קריא לצורך שילוב בפרומפט
        lines = []
        for q in self.questions:
            lines.append(f"Question {q.number} ({q.max_points} points):")
            for c in q.criteria:
                lines.append(f"  - {c.name} ({c.max_points} points): {c.description}")
        return "\n".join(lines)


# ---------- פלט הבדיקה ----------
class CriterionScore(BaseModel):
    """הציון שהתקבל בקריטריון אחד."""
    criterion: str = Field(description="Criterion name, exactly as in the rubric")
    points: int = Field(ge=0, le=100, description="Points awarded, between 0 and the criterion's max_points")


class QuestionResult(BaseModel):
    """הבדיקה של שאלה אחת: נקודות והערה."""
    question: str = Field(description="Question number, exactly as in the rubric")
    points: int = Field(ge=0, le=100, description="Points for this question = the sum of its criteria_scores")
    criteria_scores: list[CriterionScore] = Field(default_factory=list, description="Points per criterion of this question")
    comment: str = Field(description="Feedback for this question, in Hebrew")


class GradingResult(BaseModel):
    """
    מה שהמודל מחזיר בבדיקה עם מחוון.
    אין כאן ציון כולל: הקוד מחשב אותו כסכום הנקודות של השאלות (חשבון, לא שיפוט).
    אין כאן שם ואין student_id: המודל לא צריך אותם, והקוד מוסיף אותם אחר כך (פרטיות).
    """
    questions: list[QuestionResult] = Field(description="One entry for every question in the rubric")
    general_comment: str = Field(default="", description="Empty, unless the whole submission has a general problem (e.g. empty or irrelevant). In Hebrew.")
    flags: list[MODEL_FLAGS] = Field(default_factory=list, description="Flags for special cases; empty list if none apply")

    def total(self) -> int:
        # הציון הכולל = סכום הנקודות של כל השאלות
        return sum(q.points for q in self.questions)


class BasicGradingResult(BaseModel):
    """פלט הפרומפט הבסיסי, בלי מחוון. משמש רק את ניסוי 1 בהערכה ב-LangSmith."""
    score: int = Field(ge=0, le=100, description="Total score 0-100")
    comment: str = Field(description="Feedback to the student, in Hebrew")
    flags: list[MODEL_FLAGS] = Field(default_factory=list, description="Flags for special cases; empty list if none apply")


class StudentFeedback(BaseModel):
    """המשוב המלא לתלמידה: פלט המודל + מזהה, שם וציון כולל שהקוד מוסיף."""
    student_id: str
    name: str
    score: int = Field(ge=0, le=100)  # הציון הסופי, מחושב בקוד
    question_results: list[QuestionResult] = Field(default_factory=list)  # נקודות והערה לכל שאלה
    comment: str = ""  # הערה כללית (למשל "לא הוגשה תשובה" או משפט ההעתקה)
    flags: list[str] = Field(default_factory=list)  # str ולא Literal, כי גם הקוד מוסיף דגלים


class SelfCheckResult(BaseModel):
    """תוצאת הבדיקה העצמית של המודל על הבדיקה שלו."""
    passed: bool = Field(description="True if the grading is acceptable")
    reason: str = Field(description="If not passed: what exactly is wrong and must be fixed")


# ---------- החלטת המורה ----------
class TeacherAction(BaseModel):
    """מה שהמורה מחזירה מה-interrupt."""
    action: Literal["approve", "recheck"]
    recheck_ids: list[str] = Field(default_factory=list)  # student_id לבדיקה חוזרת
    edited_feedbacks: list[StudentFeedback] = Field(default_factory=list)  # שורות שהמורה ערכה
    rubric: Optional[Rubric] = None  # מחוון ערוך. אם השתנה - בודקים מחדש את כל הכיתה


# ---------- הגשה ----------
class Submission(TypedDict):
    student_id: str  # למשל S01
    name: str        # שם התלמידה (משם הקובץ). לא נשלח למודל.
    text: str        # תוכן התשובה, אחרי החלפת השם ב-ID
    content_hashes: list[str]  # טביעות אצבע לזיהוי קבצים זהים (ריקה לקובץ ריק)


# ---------- ה-State של הגרף ----------
class GradingState(TypedDict, total=False):
    # שדות לפי האפיון
    exercise_description: str
    input_dir: str  # התיקייה עם קבצי התלמידות (קלט ל-load_submissions)
    output_dir: str  # אופציונלי: לאן לשמור את דפי המשוב (ברירת מחדל: output/)
    rubric: Rubric
    submissions: list[Submission]
    feedbacks: list[StudentFeedback]
    approved_feedbacks: list[StudentFeedback]
    teacher_action: TeacherAction

    # שדות עזר לניהול הלולאות
    queue: list[str]               # student_id שעוד מחכים לבדיקה
    current_id: str                # התלמידה שנבדקת עכשיו
    current_result: Optional[GradingResult]  # הבדיקה האחרונה של התלמידה הנוכחית
    attempts: int                  # כמה ניסיונות בדיקה נעשו לתלמידה הנוכחית
    self_check_passed: bool        # האם הבדיקה העצמית האחרונה עברה
    self_check_reason: str         # הסיבה מה-self_check, מועברת לניסיון הבא

    # מידע למורה בדף הסיכום
    rubric_warning: str            # אזהרה אם המחוון לא תקין גם אחרי 2 ניסיונות
    duplicate_groups: int          # כמה קבוצות של קבצים זהים זוהו
