def is_prime(n):
    # מספר קטן מ-2 אינו ראשוני
    if n < 2:
        return False
    # מספיק לבדוק עד השורש: אם יש מחלק גדול מהשורש, יש גם מחלק קטן ממנו
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
