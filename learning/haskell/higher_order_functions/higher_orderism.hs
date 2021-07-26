{-
    As in the intro, functions can take functions as well as return functions
    this module will show some examples.
-}

{-
    Example: Apply twice. Take something and apply a function twice to it.

    Notice that the parenthesis are mandatory here. Before they were not,
    because they are right associative - i.e. output functions will take on the
    remainder of the arguments in the type signature.
-}
applyTwice :: (a -> a) -> a -> a
applyTwice f x = f (f x)

{-
    Example invocations of apply twice.
    Notice how we can use partial infix functions as an argument to apply twice
-}
sixPlusTen = applyTwice (+3) 10
prependThreeTwice = applyTwice (3:) [1]
hahaHahaHey = applyTwice ("HAHA " ++) "HEY"

{-
    Example: our implementation of zip with.
    This function is really useful in that it combines two lists by applying
    a function on each pair of elements.
    My implementation:
-}
zipWith' :: (a -> b -> c) -> [a] -> [b] -> [c]
zipWith' f xs ys =  [ f x y | (x, y) <- zip' xs ys ]
    where zip' :: [a] -> [b] -> [(a, b)]
          zip' [] _ = []
          zip' _ [] = []
          zip' (x:xs) (y:ys) = (x, y):zip' xs ys
{-
    Actual implementation:
    - bypasses the usage of zip
-}

zipWith'' :: (a -> b -> c) -> [a] -> [b] -> [c]
zipWith'' _ [] _ = []
zipWith'' _ _ [] = []
zipWith'' f (x:xs) (y:ys) = f x y : zipWith'' f xs ys

{-
    zipWith usage - element wise multiplication in a 2-D array ... yes...
    - The inner zipWith creates a partial function that multiplies two 1-D
      arrays element-wise.
    - The outer zipWith applies the 1-D array multiplcation to the each element
      of the 2-D arrays.
-}

elemwiseMult2D = zipWith'' (zipWith'' (*)) x y
    where x = [ [1, 2, 3], [2, 3, 4], [1, 1, 1] ]
          y = [ [3, 2, 1], [4, 3, 2], [1, 1, 1] ]

{-
    Example: flip - takes a function and two arguments and returns the same
    function with the arguments flipped.
    
    My answer:
    - This doesn't do anything special, it doesn't return a function since it
      simply evaluate the function with the arguments flipped
-}
flip' :: (a -> b -> c) -> b -> a -> c
flip' f x y = f y x

{-
    Actual answer:
    - here we are defining the flipped function the where clause and returning
      it instead of evaluating it.
-}
flip'' :: (a -> b -> c) -> (b -> a -> c)
flip'' f = g
    where g x y = f y x
{-
    Actual actual answer:
    - Ok so the simplified answer is the same as my answer. I accidentally got
      it right
    - What I forgot was that putting in partial arguments will return a partial
      function. So flip' func is the same as flip'' func.
-}
{-
    Flip usage example 1: zip but flip elements
    - will instead do zip "hello" [1,2,3,4,5]
-}
flipElements = flip' zip [1,2,3,4,5] "hello"
{-
    Flip usage example 2: zipWith but flip division operation on elements
-}
flipDiv = flip' (zipWith' div) [2,2..] [32,16,8,4,2]
