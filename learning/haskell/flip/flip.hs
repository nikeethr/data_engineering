type NestedDoubles   = [NestedDouble]
data NestedDouble    = FL  [Double]
                     | NFL NestedDoubles
                     deriving (Show)

-- | NFL (Nested [a])

flip_ :: NestedDouble -> NestedDouble
flip_ (FL [])           = FL []
flip_ (FL xs)           = FL [-x | x <- xs]
flip_ (NFL xs)          = NFL [flip_ x | x <- xs]
-- flip_ (NFL x: NFL xs)   = (flip_ x) : (flip_ xs)
