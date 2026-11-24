def is_prime(n):
    # מחזירה את כל הראשוניים עד n
    primes = []
    for k in range(2, n + 1):
        if all(k % d != 0 for d in range(2, k)):
            primes.append(k)
    return primes
