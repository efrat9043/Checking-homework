"""
זיהוי קבצים זהים - קוד בלבד, בלי מודל.
שני קבצים זהים אם יש בהם בדיוק אותן מילים באותו סדר.
הבדלי רווחים ושורות ריקות לא משנים. שינוי של מילה אחת = לא זהים.

לכל קובץ שתי טביעות אצבע:
1. של הטקסט המקורי - תופסת העתקה מלאה, גם כשבקובץ מופיע שם של תלמידה אחרת.
2. של הטקסט אחרי החלפת שם התלמידה עצמה ב-<NAME> - תופסת העתקה שבה רק השם שונה.
קבצים זהים אם יש להם לפחות טביעה אחת משותפת.

עונש העתקה: כל תלמידה בקבוצה מאבדת 70% מהנקודות, ובהערה נכתב משפט קבוע.
הקוד לא כותב מי העתיקה ממי. המורה יכולה לבטל או לשנות בעריכה לפני האישור.
"""
import hashlib
from collections import defaultdict
from typing import Optional

from schemas import DUPLICATE_FLAG, GradingState


def content_hash(raw_text: str) -> Optional[str]:
    """טביעת אצבע של רצף המילים. מחושבת על הטקסט המקורי (לפני החלפת השמות)."""
    # split() בלי פרמטר מפרק לפי כל סוג רווח (רווח, טאב, שורה חדשה) ומדלג על רווחים כפולים
    words = raw_text.split()
    if not words:
        return None  # קובץ ריק לא נחשב "זהה" לקובץ ריק אחר
    normalized = " ".join(words)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_duplicate_groups(submissions) -> list[list[str]]:
    """
    מחזירה קבוצות של student_id שהטקסט שלהן זהה. רק קבוצות עם 2 ומעלה.
    אם א' זהה ל-ב' וב' זהה ל-ג', שלושתן באותה קבוצה.
    """
    # כל תלמידה מתחילה כ"ראש קבוצה" של עצמה
    leader = {s["student_id"]: s["student_id"] for s in submissions}

    def find_leader(sid):
        while leader[sid] != sid:
            sid = leader[sid]
        return sid

    first_owner = {}  # טביעת אצבע -> התלמידה הראשונה שנמצאה איתה
    for s in submissions:
        for h in s["content_hashes"]:
            if h in first_owner:
                # טביעה משותפת -> מאחדים את שתי הקבוצות
                leader[find_leader(s["student_id"])] = find_leader(first_owner[h])
            else:
                first_owner[h] = s["student_id"]

    groups = defaultdict(list)
    for sid in leader:
        groups[find_leader(sid)].append(sid)
    return [sorted(g) for g in groups.values() if len(g) > 1]


PENALTY_KEEP = 0.3  # נשארים 30% מהנקודות = יורדים 70%
PENALTY_NOTE = "הקובץ שהוגש זהה לקובץ של תלמידה אחרת, ולכן הורדו 70% מהנקודות."


def apply_copy_penalty(score: int) -> int:
    """30% מהציון, מעוגל לשלם הקרוב (חצי מעוגל למעלה: 22.5 -> 23)."""
    return int(score * PENALTY_KEEP + 0.5)


def detect_duplicates(state: GradingState) -> dict:
    """צומת: לכל תלמידה בקבוצה - דגל, הורדת 70% ומשפט קבוע בהערה."""
    groups = find_duplicate_groups(state["submissions"])
    dup_ids = {sid for group in groups for sid in group}

    updated = []
    for fb in state["feedbacks"]:
        # הדגל משמש גם כסימן שהעונש כבר הופעל - כך הצומת יכול לרוץ שוב
        # (אחרי בדיקה חוזרת של תלמידה אחרת) בלי להוריד נקודות פעמיים
        if fb.student_id in dup_ids and DUPLICATE_FLAG not in fb.flags:
            fb = fb.model_copy(update={
                "score": apply_copy_penalty(fb.score),
                # המשפט נוסף להערה הכללית (שלרוב ריקה)
                "comment": "\n\n".join(p for p in [fb.comment.strip(), PENALTY_NOTE] if p),
                "flags": fb.flags + [DUPLICATE_FLAG],
            })
        updated.append(fb)

    return {"feedbacks": updated, "duplicate_groups": len(groups)}
