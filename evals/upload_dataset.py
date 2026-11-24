"""
העלאת הדאטהסט ל-LangSmith.
קורא את scores.csv ואת קבצי התשובות, ויוצר דאטהסט עם 36 דוגמאות:
  קלט (inputs)            = התרגיל + התשובה
  פלט צפוי (outputs)      = הציון האנושי, הטעות האמיתית, הרמה
שימוש (מתיקיית הפרויקט):
    .venv\\Scripts\\python.exe evals\\upload_dataset.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # כדי לייבא את llm ו-nodes מתיקיית הפרויקט

import llm  # noqa: F401,E402  - טוען את .env ומפעיל את truststore
from langsmith import Client  # noqa: E402

from nodes.loader import read_file_text  # noqa: E402

DATASET_NAME = "is-prime-grading"
DATA_DIR = ROOT / "evals" / "dataset"


def load_rows() -> list[dict]:
    """קורא את scores.csv. עוצר אם יש שורה בלי ציון אנושי."""
    with open(DATA_DIR / "scores.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    missing = [r["file"] for r in rows if not r["human_score"].strip()]
    if missing:
        sys.exit(f"חסר human_score בשורות: {missing}. לא מעלים.")
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    client = Client()

    # לא יוצרים כפילות: אם הדאטהסט כבר קיים - עוצרים
    if client.has_dataset(dataset_name=DATASET_NAME):
        sys.exit(f"הדאטהסט '{DATASET_NAME}' כבר קיים ב-LangSmith. לא יוצרים כפילות.")

    exercise = (DATA_DIR / "exercise.txt").read_text(encoding="utf-8")
    rows = load_rows()

    dataset = client.create_dataset(
        DATASET_NAME,
        description="36 תשובות לתרגיל is_prime עם ציון של מורה, בשלוש רמות: good / partial / wrong",
    )
    examples = [
        {
            "inputs": {"exercise": exercise, "answer": read_file_text(DATA_DIR / "answers" / r["file"])},
            "outputs": {"human_score": int(r["human_score"]), "real_issue": r["real_issue"], "level": r["level"]},
            "metadata": {"file": r["file"], "level": r["level"]},
        }
        for r in rows
    ]
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"נוצר הדאטהסט '{DATASET_NAME}' עם {len(examples)} דוגמאות.")


if __name__ == "__main__":
    main()
