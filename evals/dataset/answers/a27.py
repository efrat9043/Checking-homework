def is_prime(n):
    # if it is not divisible by 2 or 3 it is prime
    if n < 2:
        return False
    if n % 2 == 0 or n % 3 == 0:
        return n in (2, 3)
    return True
