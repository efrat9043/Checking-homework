# פתרון רקורסיבי: has_divisor בודקת אם יש מחלק החל מ-d ועד השורש של n.
# אם n קטן מ-2 - לא ראשוני. אחרת n ראשוני אם אין לו מחלק החל מ-2.
def has_divisor(n, d):
    if d * d > n:
        return False
    if n % d == 0:
        return True
    return has_divisor(n, d + 1)

def is_prime(n):
    if n < 2:
        return False
    return not has_divisor(n, 2)
