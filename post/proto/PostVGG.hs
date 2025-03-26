{- a model for classifying images as containing post or not -}

import Metatorch

height = lit 600
width  = lit 800
--height = var "height"
--width  = var "width"
--hidden = var "hidden"
hidden = var "hidden"
batch  = var "batch"
one    = lit 1
two    = lit 2
three  = lit 3


--compute the length the flat vector
--flat = foldr multiply hidden [lit 26, lit 32]
flat = foldr multiply hidden [lit 4, lit 5]

-- a model resembling VGG-16


--a classifier (two classess) processing one image at a time
post :: Flow
post = input [batch, three, height, width]

      --block one, two convs and a max pool
      --three channels in, "hidden" out, window size of 3, 1 stride, padding 2
      >>= conv2d 3 1 2 three hidden
      >>= relu
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= maxPool2d 2 2 1 hidden

      --block two, two convs and a max pool
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 2 2 hidden hidden
      >>= relu
      >>= maxPool2d 2 2 1 hidden

      --block three, 3 convs and a max pool
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 2 2 hidden hidden
      >>= relu
      >>= maxPool2d 2 2 1 hidden

      --block four, 3 convs and a max pool
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 2 2 hidden hidden
      >>= relu
      >>= maxPool2d 2 2 1 hidden

      --block five, 3 convs and a max pool
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 1 2 hidden hidden
      >>= relu
      >>= conv2d 3 2 2 hidden hidden
      >>= relu
      >>= maxPool2d 2 2 1 hidden

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
