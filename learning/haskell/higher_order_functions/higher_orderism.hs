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
