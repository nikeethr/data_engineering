{-|
Haskell has a static type system. Everything as a type - so everything is
resolved at compile time. Makes Haskell very safe. Haskell can infer types.
e.g.
ghci> :t 'a'  
'a' :: Char  
ghci> :t True  
True :: Bool  
ghci> :t "HELLO!"  
"HELLO!" :: [Char]  
ghci> :t (True, 'a')  
(True, 'a') :: (Bool, Char)  
ghci> :t 4 == 5  
4 == 5 :: Bool  
-}

-- :: is the 'has type of' operator
-- We can explicitly define the type of the function
removeNonUppercase :: [Char] -> [Char]
removeNonUppercase st = [ c | c <- st, c `elem` ['A'..'Z'] ]
-- Note that [Char] is the same as String so they are interchangeable

-- Multiple parameters, there is no special difference between separating inputs
-- and outputs, they all use ->
-- Note: output is always the last parameter.
addThree :: Int -> Int -> Int -> Int
addThree x y z = x + y + z

-- Int: signed integer but bounded (32 bits)

-- Integer: signed integer but can be really long... e.g. a dumb way in  C++
-- this will be stored in an array of integers and some extra arithmetic
-- operations will exist behind the scenes. Whatever way haskell does it it will
-- be slower than Int for similar reasons.
factorial :: Integer -> Integer  
factorial n = product [1..n]
reallyLongInteger = factorial 50
-- Note: Int -> Integer doesn't work even if the input can be an Int this is
-- probably because some arithmetic operations will preserve type.

-- Float: real floating point with single precision
circumference :: Float -> Float
circumference r = pi * r * 2

-- Double: real floating point with double precision
circumference' :: Double -> Double
circumference' r = pi * r * 2

-- Bool: True or False

-- Char: character represented by single quotes

-- Tuples: are types but dependent on length and types of their components. The
-- empty tuple is also a specific type with a single value i.e. ()

