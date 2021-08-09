import Chain

{-
    Lambdas: Anonymous functions that are used only once and therefore don't
    need to be declared explicitly. Usually used for small specific operations.
    Starts with \ (because it's almost like a lambda maybe). Then, -> to
    declare the function body.

    E.g. \a -> a * 100
-}

{-
    Example: Count of long chains revisited.

    Instead of having a where clause or let clause we simply write the function
    out as one of the arguments and it will have no scope beyond that.
-}

longChains' :: (Integral a) => [a] -> Int
longChains' xs = length (filter (\xs -> length xs > 15) (map chain xs))

{-
    Incorrect usage: Often times are used in place of partial functions incorrectly.
    e.g. map (+3) [1,6,3,2] vs. map (\x -> x + 3) [1,6,3,2]. Obviously (+3) and
    (\x -> x + 3) are the same thing. And using the latter is less readible
    than the partial option.
-}

{-
    Example: multiple args.
-}
multiArgLambda = zipWith (\a b -> (a * 30 + 3) / b) [1, 2, 3] [4, 5, 6]

{-
    Example: Pattern matching. However, you can't have several patterns for on
    parameter.
-}
patternMatchLambda = map (\(a,b) -> a + b) [(1,2), (3,4)]

{-
    We can infer now why type declaration is what it is.
    Note that the following are the same:
    - The second case, addThree' takes a function that takes in parameter x and
      returns a function that takes in parameter y which returns a function
      that takes in parameter z returns the 3 parameters added together
    - This is basically curried functions in action
-}
addThree :: (Num a) => a -> a -> a -> a
addThree x y z = x + y + z

addThree' :: (Num a) => a -> a -> a -> a
addThree' = \x -> \y -> \z -> x + y + z

{-
    In the above example the latter is less readible and lambdas are seldom
    used like this. However, there are cases where it makes things clearer.

    For example flip which was `flip f x y = f y x` is a bit ambigious if it's
    utility is to take a function and return a function or evaluate the
    function with the arguments.

    We can use lambdas to clarify what the purpose of the function is:
    - Here we see flip takes a function and returns a **function** that takes
      two arguments and flips them before evaluating.

    Of course this is also equivilent as seen previously to:
    flip f = g
        where g = f y x

    But lambdas are concise way to write this in order to make things explicit
    that the purpose of the function is to be partially applied
-}
flip' :: (a -> b -> c) -> b -> c
flip' f = \x y -> f y x
