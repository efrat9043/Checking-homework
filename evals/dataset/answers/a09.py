from math import isqrt

def is_prime(n):
    # אם n < 2 התשובה False.
    # any מחפשת מחלק כלשהו בין 2 לשורש; אם נמצא - n לא ראשוני.
    if n < 2:
        return False
    return not any(n % i == 0 for i in range(2, isqrt(n) + 1))
