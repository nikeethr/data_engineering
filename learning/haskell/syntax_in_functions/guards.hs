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
