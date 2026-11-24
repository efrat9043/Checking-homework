"""
טעינת ההגשות - קוד בלבד, בלי החלטות תוכן.
קורא כל קובץ בתיקייה, מחלץ טקסט, נותן ID ומחליף את שם התלמידה ב-ID.
"""
import re
from pathlib import Path

from docx import Document

from nodes.duplicates import content_hash
from schemas import GradingState, Submission

# סימון לקובץ שאי אפשר לקרוא כטקסט. המודל יחליט מה לעשות איתו (דגל "לא ניתן לבדיקה").
UNREADABLE = "<<the file could not be read as text>>"


def read_file_text(path: Path) -> str:
    """מחלצת טקסט מקובץ Word או מקובץ טקסט/קוד."""
    if path.suffix.lower() == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    data = path.read_bytes()
    if b"\x00" in data:  # בייט אפס = קובץ בינארי (תמונה, doc ישן וכו')
        return UNREADABLE
    # קודם UTF-8, ואם נכשל - הקידוד העברי של Windows
    for encoding in ("utf-8-sig", "cp1255"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return UNREADABLE


OTHER_NAME = "[שם]"  # מחליף שמות של תלמידות אחרות שמופיעים בקובץ


def anonymize(text: str, name: str, replacement: str) -> str:
    """מחליפה את השם המלא וכל חלק שלו ב-replacement (ID או מילה קבועה)."""
    parts = {name} | {p for p in re.split(r"[\s_\-]+", name) if len(p) >= 2}
    # קודם החלקים הארוכים, כדי ש"רחל כהן" יוחלף לפני "רחל"
    for part in sorted(parts, key=len, reverse=True):
        # (?<!\w)     = תחילת מילה (לפני השם אין אות או ספרה)
        # ([והבכלמש]?) = מותרת אות שימוש אחת, בשביל "ורחל", "לרחל"
        # (?!\w)      = סוף מילה, כדי ש-"Dan" לא יוחלף בתוך "Danger" ו"לאה" לא בתוך "לולאה"
        pattern = r"(?<!\w)([והבכלמש]?)" + re.escape(part) + r"(?!\w)"
        text = re.sub(pattern, lambda m: m.group(1) + replacement, text, flags=re.IGNORECASE)
    return text


def anonymize_all(text: str, own_name: str, student_id: str, other_names: list[str]) -> str:
    """השם של התלמידה עצמה -> ה-ID שלה. שמות של תלמידות אחרות -> [שם]."""
    text = anonymize(text, own_name, student_id)
    for other in other_names:
        text = anonymize(text, other, OTHER_NAME)
    return text


def load_submissions(state: GradingState) -> dict:
    """צומת: קורא את כל הקבצים ובונה את רשימת ההגשות ואת תור הבדיקה."""
    folder = Path(state["input_dir"])
    # מדלגים על קבצים נסתרים ועל קבצים זמניים של Word (~$)
    files = sorted(
        p for p in folder.iterdir()
        if p.is_file() and not p.name.startswith((".", "~$"))
    )
    if not files:
        raise ValueError(f"לא נמצאו קבצים בתיקייה {folder}")

    width = max(2, len(str(len(files))))  # S01..S99, ומעל 99 תלמידות: S001
    # שם הקובץ בלי הסיומת = שם התלמידה
    names = [p.stem.replace("_", " ").strip() for p in files]

    submissions: list[Submission] = []
    for i, (path, name) in enumerate(zip(files, names), start=1):
        student_id = f"S{i:0{width}d}"
        raw = read_file_text(path)
        # שתי טביעות אצבע: של המקור, ושל הטקסט אחרי החלפת שם התלמידה עצמה במילה קבועה
        hashes = {content_hash(raw), content_hash(anonymize(raw, name, "<NAME>"))}
        others = [n for n in names if n != name]
        submissions.append({
            "student_id": student_id,
            "name": name,
            "text": anonymize_all(raw, name, student_id, others),  # רק הטקסט הזה יישלח למודל
            "content_hashes": sorted(h for h in hashes if h is not None),  # None = קובץ ריק
        })

    return {
        "submissions": submissions,
        "feedbacks": [],
        "queue": [s["student_id"] for s in submissions],
    }
