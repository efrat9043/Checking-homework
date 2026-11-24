# שאלה 1
# אפשר לשנות tuple אבל אי אפשר לשנות list.

# שאלה 2
def count_vowels(s):
    vowels = "aeiouAEIOU"
    total = 0
    for letter in s:
        if letter in vowels:
            total += 1
    return total

# שאלה 3 - לא הספקתי
