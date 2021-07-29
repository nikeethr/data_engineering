{-
    Map takes a function and a list and applies that function to each element in the list

    Note that it is similar to list comprehension.
    [ x+3 | x <- [1,5,3,1,6] ] is the same as map (+3) [1,5,3,1,6]

    However, map can be more readible when it comes to e.g. maps of maps.
-}
map' :: (a -> b) -> [a] -> [b]
map' _ []     = []
map' f (x:xs) = f x : map' f xs

{-
    Filter takes a predicate (a function that tells if something is true or not) and a list.

    It returns a list with all the elements that satisfies the predicate.
-}
filter' :: (a -> Bool) -> [a] -> [a]
filter' _ []      = []
filter' f (x:xs)
    | f x         = x : filter' f xs
    | otherwise   = filter' f xs

{-
    Quicksort revisited.

    Similar to map, filter also can be represented via a list comprehension.
    Here is an alternate version of quicksort that uses filter which arguably
    might be more readible.
-}
quicksort' :: (Ord a) => [a] -> [a]
quicksort' []     = []
quicksort' (x:xs) = smaller ++ x : larger
    where larger  = quicksort' (filter' (>x) xs)
          smaller = quicksort' (filter' (<=x) xs)

{-
    Maps and filters are bread and butter of a functional programmer's tool box
    needed for solving complex problems by breaking them down.
-}

{-
    Example: find largest number up to 100,000 divisible by 3829
-}
largestDivisible :: Integer -> Integer -> Integer
largestDivisible x y = last [ j |  j <- [1..y], j `rem` x == 0 ]
{-
    Another way to write this, is to simply get a sequence with interval of
    3829 up to 100,000
-}
largestDivisible' :: Integer -> Integer -> Integer
largestDivisible' x y = last [x,x*2..y]
{-
    Actual answer: Using filter
    - Note traversing the list backwards is better, since haskell is lazy in
    evaluation so it will stop at the frst instance where the predicate is true
    and hence return the largest value.
    - Also using Integral type as that is more general (can apply to Int or
    Integer).

    I personally find the list comprehension more readible in this instance but
    there are other examples coming up...
-}
largestDivisible'' :: (Integral a) => a -> a -> a
largestDivisible'' x y = head (filter (p x) [y,y-1..1])
    where p i j = j `mod` i == 0

{-
    takeWhile is a function that takes function that evalulates a predicate and
    applies it to a list until the first ocurrance that predicate holds true.
    
    Basic example is extracting the first word of a sentence:
-}
elephants = takeWhile (/=' ') "elephants know how to party"

{-
    Another example: Sum of odd squares less than 10,000, used in conjunction with filter)
-}
sumOddSquares :: (Integral a) => a -> [a]
sumOddSquares x = takeWhile (< x) (filter p (map k [1..]))
    where p i = (i `mod` 2) /= 0
          k i = i * i
{-
    Actual answer:
    sum (takeWhile (<10000) (filter odd (map (^2) [1..])))

    Note:
      - `odd` is an actual function so you don't have to do `mod`
      - ^2 takes a power without making it a floating point
-}
{-
    In this case list comprehension might actually be easier to read
-}
sumOddSquares' :: (Integral a) => a -> [a]
sumOddSquares' x = takeWhile (< x) [ i*i | i <- [1..], (i*i `mod` 2) /= 0 ]
{-
    Actual awnser:
    sum (takeWhile (<10000) [n^2 | n <- [1..], odd (n^2)])  

    Note:
      - as above, note usage of `odd `and ``^
-}
