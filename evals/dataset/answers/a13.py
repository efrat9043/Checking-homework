# בודקים אם יש מחלק בין 2 לשורש של n
def is_prime(n):
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
