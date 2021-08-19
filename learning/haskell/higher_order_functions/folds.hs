{-
    folds take in a function, a accumulator (same type as the values in the
    list) and some thing to be folded (usually a list of things). The function
    applies the function to the accumulator to each element of the list. The
    output is the same type as the accumulator.

    This paradigm can help making certain recursive functions a lot more
    succint

    foldl takes the last element of xs and work backward.
      - Note the accumulator function for foldl takes the accumulated result as
        the first argument
      - use foldl' the strict option for space efficiency and finite data.
    foldr takes the first element of xs and works forward, so is lazy because
    it doesn't need to know the end of the list.
      - Note the accumulator function for foldl takes the accumulated result as
        the second argument
      - Results can be easily evaluated and hence processed intermediately.
-}

{-
    Example 1: sum
-}
sum' :: (Num a) => [a] -> a
sum' xs = foldl (\acc x -> acc + x) 0 xs

{-
    There is a simpler way to write this knowing that `+` is also a function
    and can be made a partial function. There are two aspects to this:
    1. `+` takes two arguments and ads them together this is basically the
       lambda we created previously (without the explicit accumulator argument)
    2. we don't need to provide xs as an argument as the foldl expression will
       return a partial function with one argument (xs)
    More generally anything that is foo x = bar y x can be written as foo = bar y
-}
sum'' :: (Num a) => [a] -> a
sum'' = foldl (+) 0

{-
    Example 2: elem. Check whether element is part of a list (using left fold)
    I'm guessing this actually more efficient with a right fold
-}
elem' :: (Eq a) => a -> [a] -> Bool
elem' a = foldl (\acc x -> acc || (a == x)) False

{-
    Example 3: using right fold for map (note for map we definitely want lazy
    evaluation). The type of output doesn't need to match the Foldable 'list'
    for lack of better term.

    We could implement it with foldl::

        map' f xs = foldl (\acc x -> acc ++ [f x]) [] xs

    But this `++` is a more expensive operation, furthermore, foldl will not
    work appropriately for infinite series as the outermost evaluation of foldl
    is the last element of the list which requires traversing the entire list
    (will e.g. hang on infinite lists).
-}
mapr' :: (a -> b) -> [a] -> [b]
mapr' f xs = foldr (\x acc -> f x : acc) [] xs

{-
    map using left fold for testing with infinite lists
-}
mapl' :: (a -> b) -> [a] -> [b]
mapl' f xs = foldl (\acc x -> acc ++ [f x]) [] xs
