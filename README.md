# Post Prediction
This repo holds the scripts and files related to processing the images collected
in the vineyard to be fed into the ML algorithm for predicting yield.

## Workflow:
- Collect Data with the rover at the vineyard
- Move data from GoPro SD cards to external drive/your computer using `data-collection-scripts/moveImagesAPP.py`
  - If one of the GoPros has the wrong date, you can run `data-collection-scripts/ChangeDate.py` to change the date so `moveImagesAPP.py` works better
- Run `getImagePath.py` to create a .csv file to feed into `tagrows.py`. 
- Run `row/tagrows.py` on a day of images to tag the end of each row
- Run `bay/rover_predbay.go` using the .csv file exported by `tagrows.py` and hyperparameters
- Check `predbay.go` output by running `verify/checkbays.py`


