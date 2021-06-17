{-
You can have several definitions in functions. Which allows for pattern
matching on any data type.
-}

-- Will spit out different msg if input = 7
lucky :: (Integral a) => a -> String
lucky 7 = "LUCKY NUMBER SEVEN!"
lucky x = "Out of luck :("

-- Patterns are checked top to bottom, if we swap the statements haskell will
-- spit out an error saying lucky 7 = ... is redundant

-- Factorial: recursive version
factorial :: (Integral a) => a -> a
factorial 0 = 1
factorial n = n * factorial (n - 1)
