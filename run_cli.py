"""
הרצת הגרף מהטרמינל, בלי ממשק - לבדיקה.
שימוש:
    .venv\\Scripts\\python.exe run_cli.py --input sample_data --exercise exercise.txt
"""
import argparse
import copy
import sys
import uuid
from pathlib import Path

from langgraph.types import Command

from graph import RECURSION_LIMIT, build_graph

sys.stdout.reconfigure(encoding="utf-8")  # הדפסת עברית בטרמינל של Windows


def run_until_pause(graph, graph_input, config):
    """מריץ את הגרף ומדפיס כל צומת. מחזיר את מה שה-interrupt שלח, או None אם הגרף הסתיים."""
    paused = None
    for chunk in graph.stream(graph_input, config, stream_mode="updates"):
        for node, update in chunk.items():
            if node == "__interrupt__":
                # לא יוצאים באמצע הלולאה: נותנים לריצה להסתיים מעצמה,
                # אחרת LangSmith מסמן אותה כשגיאה (GeneratorExit)
                paused = update[0].value
                continue
            extra = f" ({update['current_id']})" if update and "current_id" in update else ""
            print(f"  -> {node}{extra}")
    return paused


def print_summary(summary: dict):
    """מדפיס את דף הסיכום: מחוון, אזהרות וטבלת הכיתה."""
    print("\n===== מחוון =====")
    for q in summary["rubric"]["questions"]:
        print(f"  שאלה {q['number']} ({q['max_points']} נק'):")
        for c in q["criteria"]:
            print(f"    - {c['name']} ({c['max_points']}): {c['description']}")
    if summary["rubric_warning"]:
        print("  !! " + summary["rubric_warning"])
    if summary["duplicate_groups"]:
        print(f"\nזוהו {summary['duplicate_groups']} קבוצות של קבצים זהים. "
              "לתלמידות המסומנות הורדו 70% מהנקודות (אפשר לערוך לפני האישור).")
    print("\n===== הכיתה =====")
    for f in summary["feedbacks"]:
        flags = ", ".join(f["flags"]) or "-"
        print(f"\n[{f['student_id']}] {f['name']} | ציון: {f['score']} | דגלים: {flags}")
        for q in f["question_results"]:
            # הערה של כמה שורות מודפסת בשורה אחת, מופרדת ב-|
            print(f"  שאלה {q['question']} ({q['points']} נק'): " + q["comment"].strip().replace("\n", " | "))
        if f["comment"]:
            print("  " + f["comment"].replace("\n", " "))


def ask_teacher(summary: dict) -> dict:
    """שואל את המורה מה לעשות ומחזיר את התשובה במבנה של TeacherAction."""
    by_id = {f["student_id"]: f for f in summary["feedbacks"]}
    edited = {}
    while True:
        try:
            line = input("\nפקודה (a=אישור | r S01 S02=בדיקה חוזרת | e S01=עריכה): ")
        except EOFError:  # הקלט נגמר (למשל כשמעבירים פקודות מקובץ) - יוצאים בלי לאשר
            print("\nהקלט נגמר. יוצא בלי אישור.")
            sys.exit(1)
        # PowerShell מוסיף לפעמים תו בלתי נראה (BOM) בתחילת קלט שמועבר בצינור - מורידים אותו
        cmd = line.replace("﻿", "").strip().split()
        if not cmd:
            continue
        if cmd[0] == "a":
            return {"action": "approve", "edited_feedbacks": list(edited.values())}
        if cmd[0] == "r" and len(cmd) > 1:
            return {"action": "recheck", "recheck_ids": cmd[1:], "edited_feedbacks": list(edited.values())}
        if cmd[0] == "e" and len(cmd) == 2 and cmd[1] in by_id:
            # deepcopy: עותק מלא, כדי שהעריכה לא תשנה את המקור לפני שנשמרה
            fb = copy.deepcopy(edited.get(cmd[1], by_id[cmd[1]]))
            score = input(f"  ציון סופי חדש (Enter = להשאיר {fb['score']}): ").strip()
            if score:
                fb["score"] = int(score)
            for q in fb["question_results"]:
                comment = input(f"  הערה לשאלה {q['question']} (Enter = להשאיר): ").strip()
                if comment:
                    q["comment"] = comment
            general = input("  הערה כללית (Enter = להשאיר): ").strip()
            if general:
                fb["comment"] = general
            edited[cmd[1]] = fb
            print("  נשמר. אפשר לערוך עוד או לאשר.")
            continue
        print("  פקודה לא מוכרת.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="sample_data", help="תיקיית קבצי התלמידות")
    parser.add_argument("--exercise", default="exercise.txt", help="קובץ עם תיאור התרגיל")
    args = parser.parse_args()

    graph = build_graph()
    # thread_id מזהה את הריצה, כדי שה-checkpointer ידע מאיפה להמשיך אחרי interrupt
    config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": RECURSION_LIMIT}

    exercise = Path(args.exercise).read_text(encoding="utf-8")
    print("מתחיל בדיקה...")
    summary = run_until_pause(graph, {"exercise_description": exercise, "input_dir": args.input}, config)

    # כל עוד הגרף עצר לאישור מורה: מציגים, שואלים וממשיכים עם Command(resume=...)
    while summary is not None:
        print_summary(summary)
        answer = ask_teacher(summary)
        summary = run_until_pause(graph, Command(resume=answer), config)

    print("\nהסתיים. הדפים נשמרו בתיקייה output/")


if __name__ == "__main__":
    main()
