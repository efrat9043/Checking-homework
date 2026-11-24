# שאלה 1
# tuple היא רשימה שאי אפשר לשנות, ו-list אפשר לשנות.

# שאלה 2
def count_vowels(s):
    count = 0
    for ch in s:
        if ch in "aeiou":
            count += 1
    return count

# שאלה 3
# ממיינת ולוקחת את האיבר לפני האחרון
def second_largest(nums):
    if len(nums) < 2:
        return None
    nums = sorted(nums)
    return nums[-2]
