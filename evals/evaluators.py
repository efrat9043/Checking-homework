"""
שלושת ה-evaluators של ההערכה ב-LangSmith.
כל evaluator מקבל את הפלט של הסוכן (outputs) ואת הפלט הצפוי מהדאטהסט (reference_outputs),
ומחזיר ציון עם מפתח (key) שמופיע כעמודה ב-LangSmith.
"""
from pydantic import BaseModel, Field

from llm import get_judge_llm

# פלט של סוכן שנכשל (למשל שגיאה) מקבל את ההפרש המקסימלי, כדי שכישלון לא "ייעלם" מהממוצע
MAX_ERROR = 100


# ---------- 1. הפרש מוחלט מהציון האנושי (קוד) ----------
def abs_error(outputs: dict, reference_outputs: dict) -> dict:
    """כמה נקודות הציון של הסוכן רחוק מהציון של המורה. נמוך = טוב."""
    score = outputs.get("score")
    if not isinstance(score, int):
        return {"key": "abs_error", "score": MAX_ERROR, "comment": "לסוכן אין ציון"}
    return {"key": "abs_error", "score": abs(score - reference_outputs["human_score"])}


# ---------- 2. תקינות האובייקט (קוד) ----------
def valid_output(outputs: dict) -> dict:
    """1 אם כל השדות קיימים והציון בטווח 0-100, אחרת 0."""
    score = outputs.get("score")
    comment = outputs.get("comment")
    ok = (
        isinstance(score, int) and 0 <= score <= 100
        and isinstance(comment, str) and comment.strip() != ""
        and isinstance(outputs.get("flags"), list)
    )
    return {"key": "valid_output", "score": int(ok)}


# ---------- 3. האם ההערה מתייחסת לטעות האמיתית (LLM-as-judge) ----------
class JudgeVerdict(BaseModel):
    reasoning: str = Field(description="Short reasoning, in English")
    hits_real_issue: bool = Field(description="True if the comment matches the real issue as defined in the instructions")


JUDGE_SYSTEM = """You evaluate feedback that an automatic grader wrote on a student's answer.
You get the student's answer, the real issue (written by a teacher) and the grader's comment.
Rules:
- If the real issue is "none" (the answer is correct): hits_real_issue = true only if the comment does not
  claim any real mistake. A short positive sentence such as "תשובה מצוינת" is fine.
- Otherwise: hits_real_issue = true only if the comment identifies the real issue (the same mistake, in any wording).
  If the real issue lists several problems separated by ";", the comment must mention at least the most important one.
- A comment that mentions only other, invented or minor problems and misses the real issue: false.
Write short reasoning first, then the verdict."""

JUDGE_HUMAN = """Student answer:
{answer}

Real issue (teacher):
{real_issue}

Grader's comment:
{comment}"""


def hits_real_issue(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """שופט (מודל נפרד, JUDGE_MODEL) מחליט אם ההערה של הסוכן מתייחסת לטעות שהמורה כתבה."""
    comment = outputs.get("comment") or ""
    if not comment.strip():
        return {"key": "hits_real_issue", "score": 0, "comment": "אין הערה"}
    judge = get_judge_llm().with_structured_output(JudgeVerdict)
    verdict = judge.invoke([
        ("system", JUDGE_SYSTEM),
        ("human", JUDGE_HUMAN.format(answer=inputs["answer"], real_issue=reference_outputs["real_issue"],
                                     comment=comment)),
    ])
    return {"key": "hits_real_issue", "score": int(verdict.hits_real_issue), "comment": verdict.reasoning}


EVALUATORS = [abs_error, valid_output, hits_real_issue]
