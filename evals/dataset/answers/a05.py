def is_prime(n):
    # numbers smaller than 2 are not prime
    if n <= 1:
        return False
    k = 2
    # stop when k*k > n, which is the same as checking up to the square root
    while k * k <= n:
        if n % k == 0:
            return False
        k = k + 1
    return True
