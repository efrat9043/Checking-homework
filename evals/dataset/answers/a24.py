def is_prime(n):
    # 1 is not prime. For other numbers check divisors up to sqrt(n).
    if n == 1:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
