## Ingest

### Load_database.py

This script takes an existing image corpus and loads it into a database. The
database schema can be found [here](https://drive.google.com/open?id=1D8AfHDSQceRFKfs8WoM4yMShdO7kN7fy).

The .csv files containing image information are organized as follows:

|index|vineyard|block|date|name|time|camera|angle|lat|lon|row|bay|vine_l|vine_r|focal_length|exposure_time|
|-----|--------|-----|----|----|----|------|-----|---|---|---|---|------|------|------------|-------------|


### Initial Ingest (JPG -> CSV)

To ingest a batch of `.jpg` files use the `ingest_image.py` script.  
  1. Place the images to ingest in the appropriate folders in the `raw_images` folder of this project.  
  2. Run ```python ingest_images.py -v <vineyard> -b <block> -d <date> -i```
  3. If the script breaks at any point run the same with the `-i` flag replaced with `-p` (patch instead of ingest)
  4. The images will be renamed and relocated to the images folder specified in the `root` project.
