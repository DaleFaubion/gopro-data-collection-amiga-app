{- a model for classifying images as containing post or not -}

import Metatorch

height = lit 300
width  = lit 400
batch  = var "n"
--height = var "height"
--width  = var "width"
--hidden = var "hidden"
hidden = lit 128
one    = lit 1
two    = lit 2
three  = lit 3

--compute the length the flat vector
--flat = foldr multiply hidden [lit 9, lit 12]
flat = foldr multiply hidden [lit 5, lit 6]

-- a model resembling LeNet v5

--NOTE This is actual MK5!!!!!!!!!

--a classifier (two classess) processing one image at a time
post :: Flow
post = input [batch, three, height, width]

      --three channels in, "hidden" out, window size of 5, 2 stride, padding 2
      >>= conv2d 5 2 2 three hidden
      >>= relu

      --avg pool over window size of 2, stride of 2, padding 0
      >>= avgPool2d 2 2 0 hidden
 
      --second block
      >>= conv2d 5 2 2 hidden hidden
      >>= relu
      >>= avgPool2d 2 2 0 hidden

      >>= conv2d 5 2 2 hidden hidden
      >>= relu
      >>= avgPool2d 2 2 0 hidden

      --make the "column" image into a single vector
      >>= reshape [batch, flat]

      --MLP
      >>= linear flat hidden
      >>= relu
      >>= linear hidden hidden
      >>= relu

      --project to two classes
      >>= linear hidden two

      --loss function
      >>= crossEnt two (Vector batch)

main = evalModel post
