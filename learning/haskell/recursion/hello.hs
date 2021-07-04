{-
    Recursion is when a function is used within it's own definition. In mathematics this
    is often the case (and a neater way of writing things instead of loops since there are
    no performance considerations.) Recursion requries a edge condition to tell it when to
    stop (otherwise it'll loop for ever) and this has implications on computers since they
    have stack limitations. However, haskell executes things differently with it's lazy
    loading, so we don't really need to worry about it too much..

    Haskell's declarative approach means that you describe what something is
    rather than how to get it like imperitive languages.
-}

{-
    Case study: maximum
-}

-- My answer
maximum' :: (Ord a) => [a] -> a
maximum' []     = error "Empty list."
maximum' [x]    = x
maximum' [x,y]  = if x > y then x else y
maximum' (x:xs) = maximum' [x, maximum' xs]
-- Actual: didn't need the extra pattern [x, y] i.e.
maximum'' :: (Ord a) => [a] -> a
maximum'' []     = error "Empty list."
maximum'' [x]    = x
maximum'' (x:xs)
    | x > maxTail = x
    | otherwise = maxTail
    where maxTail = maximum'' xs
-- Even cleaner: using max which is for two elements
maximum''' :: (Ord a) => [a] -> a
maximum''' []     = error "Empty list."
maximum''' [x]    = x
maximum''' (x:xs) = max x (maximum''' xs)
{-
    Replicate: take one input and spit out out several times
    This time let's use guards
    My answer:
-}
replicate' :: a -> Int -> [a]
replicate' x n
    | n <= 0 = []
    | n == 1 = [x]
    | otherwise = x:(replicate' x (n-1))
{-
    Actual answer:
    - Again didn't need another condition as x:[] = [x] and n == 1 is covered
    - answer has (Ord i, Num i) instead of Int. Why?
    - note execution order in is okay without explicit parenthesis x:replicate' (n-1) x
-}
replicate'' :: (Ord i, Num i) => i -> a -> [a]
replicate'' n x
    | n <= 0 = []
    | otherwise = x:replicate'' (n-1) x
