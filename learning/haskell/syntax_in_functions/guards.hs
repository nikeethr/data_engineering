--- Intro to guards ---
{-
    Patterns make sure a value conforms to some form and deconstructing it.
    Guards are a way of testing whether some property of a value (or several of
    them) are true or false.
-}
bmiTell :: (RealFloat a) => a -> String
bmiTell bmi
    | bmi <= 18.5 = "thin"
    | bmi <= 25.0 = "normal"
    | bmi <= 30.0 = "fat"
    | otherwise   = "whale"

{-
    As opposed to pattern matching where you can't really do mathematical
    expressions on the function arguments, guards allow you to do this.
-}
bmiTell' :: (RealFloat a) => a -> a -> String
bmiTell' weight height
    | weight / height ^ 2 <= 18.5 = "thin"
    | weight / height ^ 2 <= 25.0 = "normal"
    | weight / height ^ 2 <= 30.0 = "fat"
    | otherwise                   = "whale"

{-
    Let's try implementing our own max function. Remember the Ord typeclass
    allows from comparisons.
-}
max' :: (Ord a) => a -> a -> a
max' a b
    | a > b     = a
    | otherwise = b
-- NOTE: you can write guards on one line but it's not recommended

{-
    Our own compare...
-}
compare' :: (Ord a) => a -> a -> Ordering
compare' a b
    | a < b     = LT
    | a > b     = GT
    | otherwise = EQ

--- Where ---
{-
    Where let's us associate names to expressions so that they can be re-used
    in the guards in order to avoid repetition. They are a syntactic construct.
    They allow access to the bindings anywhere in the guard.
-}
bmiTell1 :: (RealFloat a) => a -> a -> String
bmiTell1 weight height
    | bmi <= 18.5 = "thin"
    | bmi <= 25.0 = "normal"
    | bmi <= 30.0 = "fat"
    | otherwise   = "whale"
    where bmi = weight / height ^ 2

{-
    We can go overboard with it, but note that everything in the where clause
    needs to be aligned otherwise haskell with complain.

    Note: These where bindings are not shared across functions
-}
bmiTell2 :: (RealFloat a) => a -> a -> String
bmiTell2 weight height
    | bmi <= skinny = "thin"
    | bmi <= normal = "normal"
    | bmi <= fat = "fat"
    | otherwise   = "whale"
    where bmi = weight / height ^ 2
          skinny = 18.5
          normal = 25.0
          fat = 30.0
{-
    we can also use pattern matching for the where bindings e.g.
    ...
    where bmi = ...
          (skinny, normal, fat) = (18.5, 25.0, 30.0)
    Another example is extracting the initials from the first and last name.
-}
initials :: String -> String -> String
initials firstname lastname = f:". " ++ l:"."
    where (f:_) = firstname
          (l:_) = lastname

{-
    we don't just have to use where for defining constants we can also use it
    for defining functions.
-}
calcBmis :: (RealFloat a) => [(a, a)] -> [a]
calcBmis xs = [ calcBmi w h | (w, h) <- xs ]
    where calcBmi w h =  w / h^2

--- Let ---
{-
    Let is a like where bindings, but can be used anywhere and are expressions
    themselves but are very local and don't span across guards.

    let <bindings> in <expression>
-}
cylinder :: (RealFloat a) => a -> a -> a
cylinder r h =
    let sideArea = 2 * pi * r * h
        topArea  = pi * r^2
    in  sideArea + 2 * topArea

{-
    If statements are also expressions that can be crammed in anyhwere,
    similarly you can do that with let bindings.
-}
theQuestionToTheMeaningOfLife = 4 * (let a = 9 in a + 1) + 2

{-
    You can also introduce functions with local scope
-}
aFunctionInTheWild = [let square x = x * x in (square 5, square 3, square 2)]
