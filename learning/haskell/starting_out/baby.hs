doubleMe x = x + x
doubleUs x y = doubleMe x + doubleMe y
-- all conditions must return something
doubleSmallNumber x = if x > 100
                      then x
                      else x*2
-- ' can be used on any function - convention is 'strict'
doubleSmallNumber' x = (if x > 100 then x else x*2)  + 1
-- functions need to start with a lower-case
conanO'Brien = "It's a-me, Conan O'Brien!"
