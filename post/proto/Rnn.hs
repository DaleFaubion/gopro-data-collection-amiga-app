{- a model for classifying images as containing post or not -}

--this prototype treats images in a batch as a row or part of a row

import Metatorch

height = lit 600
width  = lit 800
batch  = var "n"
hidden = var "hidden"
two    = lit 2  --two classes
three  = lit 3  --for color channels

--compute the length the flat vector
flat = foldr multiply hidden [lit 7, lit 10]

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

      --third block
      >>= conv2d 5 2 2 hidden hidden
      >>= relu
      >>= avgPool2d 2 2 0 hidden

      --fourth mini block
      >>= conv2d 5 1 1 hidden hidden
      >>= relu

      --make the "column" image into a single vector
      >>= reshape [batch, flat]

      --use Bi-LSTM to share features across images in the batch
      >>= lstmBi flat hidden

      --MLP
      >>= linear (multiply two hidden) hidden
      >>= relu
      >>= linear hidden hidden
      >>= relu

      --project to two classes
      >>= linear hidden two

      --loss function
      >>= crossEnt two (Vector batch)

main = evalModel post
