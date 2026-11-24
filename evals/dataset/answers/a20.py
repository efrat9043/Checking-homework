def is_prime(n):
    # זוגיים אינם ראשוניים, ולכן בודקים רק מחלקים אי-זוגיים עד השורש
    if n < 2 or n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True
