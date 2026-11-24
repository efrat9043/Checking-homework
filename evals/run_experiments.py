"""
שני הניסויים על אותו דאטהסט, וטבלת השוואה.
  ניסוי 1 (baseline-no-rubric): פרומפט בסיסי "בדוק ותן ציון", בלי מחוון.
  ניסוי 2 (with-rubric):        מחוון מפורש + הוראות לכל קריטריון + בדיקה עצמית (כמו באפליקציה).
שימוש (מתיקיית הפרויקט):
    .venv\\Scripts\\python.exe evals\\run_experiments.py            # שני הניסויים
    .venv\\Scripts\\python.exe evals\\run_experiments.py baseline   # רק ניסוי 1
    .venv\\Scripts\\python.exe evals\\run_experiments.py rubric     # רק ניסוי 2
    .venv\\Scripts\\python.exe evals\\run_experiments.py baseline v2   # ניסוי 1 בשם חדש (baseline-no-rubric-v2)
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))                    # llm, nodes, schemas
sys.path.insert(0, str(Path(__file__).parent))   # evaluators

import llm  # noqa: F401,E402  - טוען את .env ומפעיל את truststore
from langsmith import Client  # noqa: E402

from evaluators import EVALUATORS  # noqa: E402
from nodes.grading import final_question_results, grade_answer_basic, grade_with_self_check  # noqa: E402
from nodes.rubric import generate_rubric  # noqa: E402
from upload_dataset import DATA_DIR, DATASET_NAME  # noqa: E402

STUDENT_ID = "S01"  # בדאטהסט אין שמות; ID קבוע
RESULTS_FILE = ROOT / "evals" / "results.json"
RUBRIC_FILE = ROOT / "evals" / "rubric_used.json"


# ---------- ניסוי 1: פרומפט בסיסי ----------
def baseline_target(inputs: dict) -> dict:
    r = grade_answer_basic(inputs["exercise"], inputs["answer"], STUDENT_ID)
    return {"score": r.score, "comment": r.comment, "flags": list(r.flags)}


# ---------- ניסוי 2: מחוון + בדיקה עצמית ----------
def make_rubric_target(rubric):
    """מחזירה פונקציית target שמשתמשת באותו מחוון לכל הדוגמאות (כמו בכיתה אמיתית)."""
    def target(inputs: dict) -> dict:
        result, passed = grade_with_self_check(inputs["exercise"], inputs["answer"], STUDENT_ID, rubric)
        questions = final_question_results(result, rubric)  # אותו חישוב כמו באפליקציה (כולל בונוס)
        comment = "\n".join(f"שאלה {q.question}: {q.comment.strip()}" for q in questions)
        if result.general_comment.strip():
            comment += "\n" + result.general_comment.strip()
        return {
            "score": min(100, sum(q.points for q in questions)),
            "comment": comment,
            "flags": list(result.flags),
            "self_check_passed": passed,
        }
    return target


def run(client: Client, target, prefix: str) -> dict:
    """מריץ ניסוי אחד ב-LangSmith ומחזיר סיכום מספרי."""
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix=prefix,
        max_concurrency=4,
        metadata={"agent_model": os.getenv("LLM_MODEL"), "judge_model": os.getenv("JUDGE_MODEL")},
    )
    scores = defaultdict(list)           # key -> כל הציונים
    error_by_level = defaultdict(list)   # level -> הפרשים
    for row in results:
        level = row["example"].outputs["level"]
        for ev in row["evaluation_results"]["results"]:
            if ev.score is None:
                continue
            scores[ev.key].append(ev.score)
            if ev.key == "abs_error":
                error_by_level[level].append(ev.score)

    def mean(xs):
        return round(sum(xs) / len(xs), 1) if xs else None

    def pct(xs):
        # אחוז מהממוצע המדויק (בלי עיגול מוקדם - אחרת 32/36 יוצא 90% במקום 88.9%)
        return round(100 * sum(xs) / len(xs), 1) if xs else None

    return {
        "experiment": results.experiment_name,
        "abs_error": mean(scores["abs_error"]),
        "abs_error_by_level": {lvl: mean(v) for lvl, v in sorted(error_by_level.items())},
        "valid_output_pct": pct(scores["valid_output"]),
        "hits_real_issue_pct": pct(scores["hits_real_issue"]),
    }


def print_table(summary: dict):
    """טבלת השוואה בין הניסויים."""
    names = list(summary)
    rows = [("הפרש ממוצע מהציון האנושי (נמוך = טוב)", lambda s: s["abs_error"])]
    for lvl in ("good", "partial", "wrong"):
        rows.append((f"   הפרש ממוצע - {lvl}", lambda s, lvl=lvl: s["abs_error_by_level"].get(lvl)))
    rows += [
        ("פלט תקין (%)", lambda s: s["valid_output_pct"]),
        ("ההערה מתייחסת לטעות האמיתית (%)", lambda s: s["hits_real_issue_pct"]),
    ]
    print("\n" + "מדד".ljust(42) + "".join(n.ljust(22) for n in names))
    print("-" * (42 + 22 * len(names)))
    for label, get in rows:
        print(label.ljust(42) + "".join(str(get(summary[n])).ljust(22) for n in names))
    print()
    for n in names:
        print(f"{n}: הניסוי ב-LangSmith נקרא {summary[n]['experiment']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    # סיומת אופציונלית לשם הניסוי (למשל v2), כדי לא לדרוס תוצאות של ניסוי קודם
    suffix = f"-{sys.argv[2]}" if len(sys.argv) > 2 else ""
    client = Client()
    if not client.has_dataset(dataset_name=DATASET_NAME):
        sys.exit("הדאטהסט לא קיים. קודם להריץ evals\\upload_dataset.py")

    # תוצאות קודמות נשמרות, כדי שאפשר להריץ ניסוי אחד בכל פעם ועדיין לקבל השוואה
    summary = json.loads(RESULTS_FILE.read_text(encoding="utf-8")) if RESULTS_FILE.exists() else {}

    if which in ("both", "baseline"):
        name = "baseline-no-rubric" + suffix
        print(f"מריץ ניסוי: {name} ...")
        summary[name] = run(client, baseline_target, name)

    if which in ("both", "rubric"):
        exercise = (DATA_DIR / "exercise.txt").read_text(encoding="utf-8")
        rubric, warning = generate_rubric(exercise)  # מחוון אחד לכל הניסוי
        if warning:
            print("אזהרה:", warning)
        RUBRIC_FILE.write_text(rubric.model_dump_json(indent=2), encoding="utf-8")
        name = "with-rubric" + suffix
        print(f"מריץ ניסוי: {name} ... (המחוון נשמר ב-evals/rubric_used.json)")
        summary[name] = run(client, make_rubric_target(rubric), name)

    RESULTS_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print_table(summary)


if __name__ == "__main__":
    main()
