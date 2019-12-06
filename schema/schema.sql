


CREATE TABLE bay
(
  id				SERIAL PRIMARY KEY,
  bay_num		INTEGER NOT NULL,
  row_num		INTEGER NOT NULL,
  block_num		INTEGER NOT NULL,
  vineyard_id	TEXT NOT NULL
);

CREATE TABLE image
(
  id				SERIAL PRIMARY KEY,
  bay_id			INTEGER NOT NULL,
  date			DATE NOT NULL,
  lat				TEXT NOT NULL,
  long			TEXT NOT NULL,
  image_binary	bytea NOT NULL,
  foreign key (bay_id) references bay (id)
);

CREATE TABLE yield
(
  bay_id		INTEGER NOT NULL,
  yield_date	DATE NOT NULL,
  yield_units	TEXT NOT NULL,
  yield_weight	TEXT NOT NULL,
  foreign key (bay_id) references bay (id)
);


/*
Creates a view combining bayes and images
*/
CREATE VIEW bay_image AS
SELECT bay_num, row_num, block_num, vineyard_id, image_binary, date
FROM bays, images, yeild
WHERE bays.bay_id = image.bay_id and bays.bay_id = yield.bay_id;
