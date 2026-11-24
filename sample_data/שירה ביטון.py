# שירה ביטון
import math

def is_prime(n):
    # כל מספר קטן מ-2 אינו ראשוני
    # all מחזירה True רק אם אף מספר בטווח לא מחלק את n
    # הטווח הוא עד השורש של n כולל, כי אם יש מחלק גדול מהשורש יש גם מחלק קטן ממנו
    return n >= 2 and all(n % d != 0 for d in range(2, math.isqrt(n) + 1))
