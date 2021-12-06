
compound :: Float -> Float -> Float -> Float -> Int -> Float
compound n k q r 0 = 0
compound n k q r i = (n * (1 + q) / k) + ((compound n k q r (i-1)) * ((1 + r) ** (15 / k)))
