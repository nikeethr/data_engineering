{-
    Function application ($):
    Takes two expressions separated by `$` and applies the expression right-associatively.
    As opposed to space ` ` which applies expressions left-associative::

    ($) :: (a -> b) -> a -> b
    f $ g = f g

    In other words, everything before the `$` (f) takes as argument the expression after
    `$` (g). So it expects g to be evaluated first.

    `$` can be thought of as the lowest precedence operator.

    Example::

    sum (filter (> 10) (map (*2) [2..10])) is equivilent to:
    f (g x (h y z)) which can be written as f $ g x $ h y z, i.e.:
    sum $ filter (>10) $ map (*2) [2..10]

    `$` itself is a function so it can also be used to do things like map a scalar value
    over a list of functions

    Example::

    map ($ 3) [(4+), (10*), (^2), sqrt]
-}

