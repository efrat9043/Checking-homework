def is_prime(n):
    # 0, 1 ומספרים שליליים אינם ראשוניים
    if n < 2:
        return False
    limit = int(n ** 0.5)
    # בודקים כל מחלק אפשרי עד השורש (כולל)
    for divisor in range(2, limit + 1):
        if n % divisor == 0:
            return False
    return True
