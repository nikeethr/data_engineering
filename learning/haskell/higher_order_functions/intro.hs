{-
    Higher order function: A function that can take functions as parmaters
    and/or return a function.

    One of standard haskell techniques to solve problems.

    Haskell functions can only take 1 parameter. The reason why we were able to
    provide multiple is due to curried functions

    e.g.
    max 4 5 is the same as (max 4) 5. (max 4) is the resultant function that
    either returns 4 or the parameter (5)

    so
      max :: (Ord a) => a -> a -> a
    can also be written as:
      max :: (Ord a) => a -> (a -> a)
    The latter is max takes an argument of type a and returns a function that
    takes an argument of type a and returns an argument of type a.

    If not all arguments are provided you get a partially applied function.
-}

{-
    Example: partially applied functions. We can split out the partially
    applied functions based on use-cases
-}
multThree :: (Num a) => a -> a -> a -> a
multThree x y z = x * y * z
multTwo_12   = multThree 12
multOne_12_5 = multTwo_12 5
mult_12_5_3  = multOne_12_5 3 

{-
    Example: compare with 100, and type declaration.

    compare has type declaration (Ord a) => a -> a -> Ordering  [1]
    which can be treated as (Ord a) => a -> (a -> Ordering)     [2]

    So it follows that if we want to compare with 100 we can either do it this
    way:
-}
compareWithHundred :: (Ord a, Num a) => a -> Ordering
compareWithHundred x = compare x 100
{-
    But instead we could evaluate to a partially applied function. Note that
    the type definition is the same since the partial application of compare
    matches the type definition (a -> Ordering) see [2].
-}
compareWithHundred' :: (Ord a, Num a) => a -> Ordering
compareWithHundred' = compare 100

{-
    Example: infix functions (e.g. `/` as in 200 / 100)

    These can also be made partial by wrapping them with parentheses and only
    providing one side.
-} 
divide10 :: (Floating a) => a -> a
divide10 = (/10)

{-
    Example: Here's infix with elem (is uppercase alphabet)
-}
isUpperAlphanum :: Char -> Bool
isUpperAlphanum = (`elem` ['A'..'Z'])

{-
    NOTE: on ghci if you try to declare a partial function without `let`, it'll
    error out because Functions aren't instances of Show
-}
