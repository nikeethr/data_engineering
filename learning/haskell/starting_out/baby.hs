---------------
-- Functions --
---------------
doubleMe x = x + x
doubleUs x y = doubleMe x + doubleMe y
-- all conditions must return something
doubleSmallNumber x = if x > 100
                      then x
                      else x*2
-- ' can be used on any function - convention is 'strict'
doubleSmallNumber' x = (if x > 100 then x else x*2)  + 1
-- functions need to start with a lower-case
conanO'Brien = "It's a-me, Conan O'Brien!"

-----------
-- Lists --
-----------
-- in the script use `let` in front to declare variable
lostNumbers = [4, 8, 15, 16, 23, 42]
-- concat numbers
a = [1, 2, 3, 4]; b = [9, 10, 11, 12]
c = a ++ b
-- concat strings
helloWorld = "hello" ++ " " ++ "world"
woot = ['w', 'o'] ++ ['o', 't']
-- NOTE: `++` takes time, use `:` to put something at the beginning
smallCat = 'A':" SMALL CAT"
putInFront = 0:[1, 2, 3, 4, 5]
-- NOTE: `:` unlike `++` takes an element of a type rather than a list of type
-- append to back still needs to use list like operation as it needs to
-- traverse the linked list
putBehind = [1, 2, 3, 4, 5] ++ [6]
-- pop out list `!!`
-- NOTE: This can be slow as the linked list needs to be re-formed use `tail`
-- instead to just view the element.
popLetter = "Nikeeth" !! 3
popNumber = [1.1, 2.2, 3.3, 4.4] !! 2
-- List of lists
-- NOTE: each list can be varying length unlike a 2-D matrix
listOfLists = [[1, 2, 3, 4], [5, 2], [1, 9, 1]]
-- notice that because we're appending a list of list as append requires a list
-- of 'type' and type happens to be a list
listOfLists1 = listOfLists ++ [[1, 1, 1, 1]]
-- note cons operator only requires a list as this is the 'type'
listOfLists2 = [6, 6, 6]:listOfLists1

-- comparisons (commented out as these are expressions)
-- list comparisons done head -> tail (lexicographical order)
-- ghci> [3,2,1] > [2,1,0]
-- True
-- ghci> [3,2,1] > [2,10,100]
-- True
-- ghci> [3,4,2] > [3,4]
-- True
-- ghci> [3,4,2] > [2,4]
-- True
-- ghci> [3,4,2] == [3,4,2]
-- True

-- Common operators
-- head: first element
headOfList = head [5, 4, 3, 2, 1]
-- tail: everything but first element
tailOfList = tail [5, 4, 3, 2, 1]
-- last: last element
lastOfList = last [5, 4, 3, 2, 1]
-- init: everything but last element
initOfList = init [5, 4, 3, 2, 1]
-- length
lengthOfList = length [5, 4, 3, 2, 1]
-- null: check if list is empty
emptyList = null []
-- reverse
reverseList = reverse [5, 4, 3, 2, 1]
-- take: extracts certain number of elements from the beginning of list
takeThreeFromList = take 3 [5, 4, 3, 2, 1]
-- drop: flip side of take, drop number of elements from beginning of list
dropThreeFromList = drop 3 [5, 4, 3, 2, 1]
-- maximum
maxOfList = maximum [8, 4, 2, 1, 5, 6]
-- minimum
minOfList = minimum [9, 2, 1, 3, 4]
-- sum
sumList = sum [1, 2, 3, 4, 5]
-- product: multiplies all elements of list together
multiplyList = product [4, 3, 2, 1]
-- elem: check if element is in list
elemInList = 4 `elem` [3, 4, 5, 6]
elemInList2 = elem 10 [3, 4, 5, 6]

------------
-- Ranges --
------------
countTo20 = [1..20]
lowerCaseAlphabets = ['a'..'z']
upperCaseKToZ = ['K'..'Z']
evenStep = [2,4..20]
threeStep = [3,6..20]
-- NOTE: floating point numbers are not precise and their use in ranges can
-- cause issues
decimalStep = [0.1,0.3..1]
-- cycle: like python generators - creates infinite repeated pattern from a list
tenOneTwoThrees = take 10 (cycle [1,2,3])
threeLOLs = take 11 (cycle "LOL ")
-- repeat: like cycling but only with 1 element
repeatFive = take 10 (repeat 5)
-- replicate is a simpler option for this sometimes
replicateTen = replicate 3 10

------------------------
-- List comprehension --
------------------------
-- It's set theory, for complex functions applied on lists with a predicate
-- S = [ 2*x | x <- N, x <= 10 ]
xSquared = [ x*2 | x <- [1..10] ]
-- adding predicate
xSquaredLarge = [ x*2 | x <- [1..10], x*2 >= 12 ]
-- more complex conditions
remThree = [ x | x <- [50..100], x `mod` 7 == 3 ]
-- conditional statement: take a list, find all odd values in the list, spit
-- out BOOM! for values less than 10 or BANG! for those greater than or equal
-- to 10: Also this is a function
boomBangs xs = [ if x < 10 then "BOOM!" else "BANG!" | x <- xs, odd x ]
-- multiple predicates: Union of predicates
multiplePredicates = [ x | x <- [10..20], x /= 13, x /= 15, x /= 19 ]
-- product all pair of elements in list
productList = [ x*y | x <- [2,5,10], y <- [8,10,11] ]
-- only greater than 50
productListLarge = [ x*y | x <- [2,5,10], y <- [8,10,11], x*y > 50 ]
-- strings?: adjective + noun
nouns = ["artist","donkey","carrot"]
adjectives = ["beautiful","lazy","vengeful"]
phrases = [ y ++ " " ++ x | x <- nouns, y <- adjectives ]
-- alternate version of length
-- NOTE: _ is a placeholder for a unused variable (similar to other languages)
length' xs = sum [1 | _ <- xs]
-- strings are lists, so these operations apply to them
-- example: remove non-uppercase
removeNonUppercase st = [ c | c <- st, c `elem` ['A'..'Z'] ]
-- nested comprehension
xxs =
  [ [1,3,5,2,3,1,2,4,5]
  , [1,2,3,4,5,6,7,8,9]
  , [1,2,3,4,5,6,7,8,9]
  ]
-- beats a double forloop huh
filterEven = [ [ x | x <- xs, even x ] | xs <- xxs ]

------------
-- Tuples --
------------
{- | Tuples are like lists but they can store different types. However, the
typing is stricter. So while you can do [[1,2], [1,2,3], [4,5]]. A Tuple
pair is it's own type so you can't do [(1,2), (3,4,5), (5,6)]. They all
need to be pairs or triples, but not a mix.

NOTE: Tuples can have more than 2 elements. More on how to access those
later.
-}
fstTuple = fst (8,11)
sndTuple = snd (8,11)
-- zip: combines two lists into a list of tuples
zipExample1 = zip [1,2,3,4,5] [5,5,5,5,5]
-- different lengths & types
zipExample2 = zip [1,2,3,4,5] ["hello","world"]
-- infinite list: similar to cycle
zipExample3 = zip [1..] ["apple","orange","cherry","mango"]
