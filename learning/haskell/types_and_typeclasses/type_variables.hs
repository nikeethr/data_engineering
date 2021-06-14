{-|
  Abstraction of variable typing.
  e.g.
  head :: [a] -> a
  'a' can represent anything, so it is of 'variable' type. Hence, it is a type variable.
-}

{-|
  Typclasses: a interface that defines some behaviour. They are not object
  oriented classes. They are like java type interfaces but better.
  e.g. 
  (==) :: (Eq a) => a -> a -> Bool
  Everything before => is a class constraint. The function == takes two
  arguments and returns a Bool. The two arguments must be the same type and
  a member of the Eq class
-}


-- Eq: Any type that supports equality. Need to implement == and /=. All types
-- mentioned so far can be tested for equality

-- Ord: used for ordering. Need to implement <, >, >=, <=. `compare` takes two
-- `Ord` members of the same type and returns an Ordering. Ordering is a type.
-- It can be GT, LT or EQ. All types mentioned so far are part of Ord.

-- Show: can be represented as strings.

-- Read: Opposite of show, takes a string and returns the type that is a member
-- of Read. Read needs to be able to infer the type, on it's own it can be
-- ambigious e.g. read "4". Can use explicit type annotations to tell read what
-- it should be. e.g. read "4" :: Int

-- Enum: sequentially ordered types. Can be used with ranges. `succ` and `pred`
-- functions can also be used. Example types: (), Bool, Char, Ordering, Int,
-- Integer, Float and Double

-- Bounded: have lower adn upper bound. You can use minBound :: Type or
-- maxBound :: Type to get the boundaries of particular types. They also work
-- on Tuples. e.g. maxBound :: (Bool, Int, Char)

-- Num: Numeric typeclass. Members can act like numbers e.g. as you would
-- expect various arithmetic operations to be performed on them.
