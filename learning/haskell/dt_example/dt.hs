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
    | 0 <= h && h < thresholdHours = proceed
    | h < 0 = wait
    | otherwise = skip
    where
        xUTC = parseUTCTime x
        yUTC = parseUTCTime y
        h = xUTC `diffHours` yUTC
        proceed = (True, fromList [("action", "proceed")])
        skip = (True, fromList [("action", "skip")])
        wait = (False, M.empty)
        thresholdHours = 12
        diffHours :: UTCTime -> UTCTime -> Float
        diffHours x y = ((fromIntegral $ fst $ properFraction $ x `diffUTCTime` y) :: Float) / 3600

-- utcX = parseUTCTime
-- utcY = parseUTCTime
-- hoursThreshold = 12
