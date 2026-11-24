# שאלה 1
# list ניתנת לשינוי (אפשר להוסיף, למחוק ולשנות איברים), ואילו tuple אינה ניתנת לשינוי אחרי שנוצרה.

# שאלה 2
def count_vowels(s):
    return sum(1 for ch in s.lower() if ch in "aeiou")

# שאלה 3
# הגישה: מסירים כפילויות עם set, ממיינים מהגדול לקטן ומחזירים את האיבר השני אם קיים.
def second_largest(nums):
    unique = sorted(set(nums), reverse=True)
    if len(unique) < 2:
        return None
    return unique[1]
