import math

def is_prime(n):
    """Returns True if n is prime. Numbers below 2 are not prime.
    We test every divisor between 2 and isqrt(n); if none divides n, it is prime."""
    if n < 2:
        return False
    for d in range(2, math.isqrt(n) + 1):
        if n % d == 0:
            return False
    return True
