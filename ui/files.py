"""
שמירת הקבצים שהמורה מעלה: קבצים בודדים או zip.
מתוך zip נשמרים רק הקבצים עצמם (בלי תיקיות), כדי ששם הקובץ יהיה שם התלמידה.
"""
import zipfile
from pathlib import Path

SKIP_PARTS = {"__MACOSX"}


def _zip_name(info: zipfile.ZipInfo) -> str:
    """שם קובץ בתוך zip. zip של Windows שומר שמות בעברית בקידוד ישן, ולכן מנסים כמה קידודים."""
    if info.flag_bits & 0x800:  # השם כבר שמור ב-UTF-8
        return info.filename
    raw = info.filename.encode("cp437")
    for encoding in ("utf-8", "cp862", "cp1255"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return info.filename


def _unique(path: Path) -> Path:
    """אם כבר קיים קובץ בשם הזה - מוסיפים מספר, כדי לא לדרוס."""
    if not path.exists():
        return path
    i = 2
    while (candidate := path.with_name(f"{path.stem} ({i}){path.suffix}")).exists():
        i += 1
    return candidate


def _keep(name: str) -> bool:
    # מדלגים על קבצים נסתרים, קבצים זמניים של Word ותיקיות מערכת של mac
    base = Path(name).name
    return bool(base) and not base.startswith((".", "~$")) and not (set(Path(name).parts) & SKIP_PARTS)


def save_uploads(uploaded_files, dest: Path) -> list[str]:
    """שומרת את הקבצים בתיקייה dest ומחזירה את שמות הקבצים שנשמרו."""
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for uf in uploaded_files:
        if uf.name.lower().endswith(".zip"):
            with zipfile.ZipFile(uf) as z:
                for info in z.infolist():
                    name = _zip_name(info)
                    if info.is_dir() or not _keep(name):
                        continue
                    target = _unique(dest / Path(name).name)  # רק שם הקובץ - בלי נתיבים מתוך ה-zip
                    target.write_bytes(z.read(info))
                    saved.append(target.name)
        elif _keep(uf.name):
            target = _unique(dest / Path(uf.name).name)
            target.write_bytes(uf.getvalue())
            saved.append(target.name)
    return sorted(saved)


def copy_folder(src: Path, dest: Path) -> list[str]:
    """מעתיקה תיקיית דוגמה (למשל sample_data_multi) לתיקיית הריצה."""
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for p in sorted(src.iterdir()):
        if p.is_file() and _keep(p.name):
            (dest / p.name).write_bytes(p.read_bytes())
            saved.append(p.name)
    return saved
