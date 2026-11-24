def is_prime(n):
    # בודקים מחלקים עד השורש
    if n < 2:
        return False
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
