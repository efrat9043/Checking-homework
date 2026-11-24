# הסבר: בודקים מחלקים רק עד השורש של n, כי מעבר לשורש אין צורך לבדוק.
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
