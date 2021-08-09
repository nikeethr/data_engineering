module Compound where
{-
    Args:
        interest rate (Float)
        investment per year (Float)
        initial amount (Float)
        number of years (Int)
    Ret:
        total capital (Float)
-}
compound :: Float -> Float -> Float -> Int -> Float
compound r x xi 0 = xi
compound r x xi n = x + (r + 1) * compound r x xi (n - 1)
