module Chain
( chain
) where
{-
    Chain creates a sequence based on certain conditions (Collatz sequences)
    It stops when the result is 1
-}
chain :: (Integral a) => a -> [a]
chain 1 = [1]
chain n
    | odd n = n : chain (n * 3 + 1)
    | otherwise = n : chain (n `div` 2)

{-
    How many chains starting between 1-100 have length greater than 15
-}
longChains :: (Integral a) => [a] -> Int
longChains xs = length (filter isLong (map chain xs))
    where isLong xs = length xs > 15
