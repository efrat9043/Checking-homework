import math

# שורה אחת: n ראשוני אם הוא לפחות 2 ואף מספר מ-2 עד השורש לא מחלק אותו
def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))
