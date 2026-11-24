# עוברים פעם אחת על הרשימה ושומרים את הגדול ביותר ואת השני בגודלו.
# מספר ששווה לגדול ביותר לא נספר, וכך מתעלמים מכפילויות.
def second_largest(nums):
    first = None
    second = None
    for x in nums:
        if first is None or x > first:
            second = first
            first = x
        elif x != first and (second is None or x > second):
            second = x
    return second
