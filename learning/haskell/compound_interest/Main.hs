module Main where
import Compound ( compound )
import GHC.Float ( int2Float, float2Int )

main :: IO ()
main = putStrLn $ show $ [ i * 700 * 12 | i <- [0..10], let r = compound 0.20 (700 * 12) 0 (float2Int i) ]
