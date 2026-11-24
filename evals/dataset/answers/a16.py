def is_prime(n):
    # לא ראשוני אם קטן מ-2. בודקים מחלקים עד השורש.
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5)):
        if n % i == 0:
            return False
    return True
