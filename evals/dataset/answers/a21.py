def is_prime(n):
    # numbers below 2 are not prime; test divisors up to the square root
    if n < 2:
        print(False)
        return
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            print(False)
            return
    print(True)
