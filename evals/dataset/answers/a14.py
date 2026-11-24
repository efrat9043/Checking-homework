def is_prime(n):
    # numbers below 2 are not prime; otherwise look for a divisor between 2 and n-1
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
