import Data.Time.Clock
import Data.Time.Format
import Data.Time.LocalTime
import Data.HashMap.Strict as M
import Data.Maybe

-- Maybe because ParseTimeM could error out
parseUTCTime :: String -> UTCTime
parseUTCTime x = fromJust (parseTimeM True defaultTimeLocale "%Y%m%dT%H%Z" (x ++ "UTC"))

checkTimeThreshold :: String -> String -> (Bool, M.HashMap String String)
checkTimeThreshold x y
    | (xUTC `hoursDiff` yUTC) < thresholdHours = (True, fromList [("1", "2"), ("3", "4")])
    | otherwise = (False, M.empty)
    where
        xUTC = parseUTCTime x
        yUTC = parseUTCTime y
        thresholdHours = 12
        hoursDiff :: UTCTime -> UTCTime -> Float
        hoursDiff x y = ((fromIntegral $ fst $ properFraction $ x `diffUTCTime` y) :: Float) / 3600

-- utcX = parseUTCTime
-- utcY = parseUTCTime
-- hoursThreshold = 12
