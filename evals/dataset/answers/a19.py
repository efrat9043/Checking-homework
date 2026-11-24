# עוברים על כל המספרים עד n ובודקים אם מישהו מחלק את n
def is_prime(n):
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
