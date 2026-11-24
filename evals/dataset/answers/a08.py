def is_prime(n):
    # Explanation: every prime > 3 has the form 6k-1 or 6k+1,
    # so after handling 2 and 3 we only test i and i+2 for i = 5, 11, 17, ... up to sqrt(n).
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
