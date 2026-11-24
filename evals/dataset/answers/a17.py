def is_prime(n):
    # numbers smaller than 1 are not prime. check divisors up to sqrt(n)
    if n < 1:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
