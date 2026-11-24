"""
הסבר על הפתרון:
מגדירים משתנה found שמציין אם מצאנו מחלק. עוברים על כל המספרים מ-2 ועד השורש של n.
אם אחד מהם מחלק את n בלי שארית, found נהיה True ועוצרים.
בסוף n ראשוני רק אם הוא לפחות 2 ולא נמצא מחלק.
"""
def is_prime(n):
    found = False
    i = 2
    while i * i <= n and not found:
        if n % i == 0:
            found = True
        i += 1
    return n >= 2 and not found
