package main

import "testing"

func SimpleImage() Image {
	img := Image{
		"test/pic/foo.jpg",
		"2024-05-20",
		"13:07:00",
		false,
		1,
		1,
		"West",
	}

	return img
}

func SecondImage() Image {
	img := Image{
		"test/pic/foo2.jpg",
		"2024-05-21",
		"13:024:00",
		true,
		1,
		2,
		"East",
	}

	return img
}

func ThirdImage() Image {
	img := Image{
		"test/pic/foo2.jpg",
		"2024-05-21",
		"13:024:00",
		true,
		1,
		3,
		"West",
	}

	return img
}

func TestRow_AppendImage_Empty(t *testing.T) {
	row := Row{}
	row = row.appendImage(SimpleImage())

	if len(row.images) != 1 || row.images[0] != SimpleImage() {
		t.Error("Image was not added to an empty row")
	}
}

func TestRow_AppendImage(t *testing.T) {
	row := Row{}
	row.images = append(row.images, SimpleImage())

	row = row.appendImage(SecondImage())

	if len(row.images) != 2 || row.images[0] != SimpleImage() || row.images[1] != SecondImage() {
		t.Error("Image was not added to a row with images")
	}
}

func TestRow_GiveToStartOf_Empties(t *testing.T) {
	left := Row{}
	right := Row{}

	left = left.appendImage(SimpleImage())
	left, right = left.giveToStartOf(&right)

	if len(left.images) != 0 {
		t.Error("Giving row did not remove image")
	}

	if len(right.images) != 1 || right.images[0] != SimpleImage() {
		t.Error("Receiving row did not add image")
	}
}

func TestRow_GiveToStartOf(t *testing.T) {
	left := Row{}
	right := Row{}

	left = left.appendImage(SimpleImage())
	left = left.appendImage(ThirdImage())
	right = right.appendImage(SecondImage())

	left, right = left.giveToStartOf(&right)

	if len(left.images) != 1 || left.images[0] != SimpleImage() {
		t.Error("Giving row does not have the correct images after giveToStartOf")
	}

	if len(right.images) != 2 || right.images[0] != ThirdImage() || right.images[1] != SecondImage() {
		t.Error("Receiving row did not add image")
	}
}

func TestRow_HasImages_NonEmpty(t *testing.T) {
	row := Row{}
	row = row.appendImage(SimpleImage())

	if !row.hasImages() {
		t.Error("Row did not have images")
	}
}

func TestRow_HasImages_Empty(t *testing.T) {
	row := Row{}

	if row.hasImages() {
		t.Error("Empty row reported to have images")
	}
}

func TestRow_TakeFromStartOf(t *testing.T) {

	left := Row{}
	right := Row{}

	left = left.appendImage(SimpleImage())
	right = right.appendImage(ThirdImage())
	right = right.appendImage(SecondImage())

	left, right = left.takeFromStartOf(&right)

	if len(left.images) != 2 || left.images[1] != ThirdImage() {
		t.Error("The receiving row did not add the image")
	}

	if len(right.images) != 1 || right.images[0] != SecondImage() {
		t.Error("The giving row did not have the correct number of images")
	}
}

func TestRow_NumEmpty(t *testing.T) {
	row := Row{}
	row = row.appendImage(SimpleImage())
	row = row.appendImage(SecondImage())
	row = row.appendImage(ThirdImage())

	if row.numRegular() != 1 {
		t.Error("Row did not have the correct number of non-post images")
	}
}

func TestRow_NumImages(t *testing.T) {
	row := Row{}
	row = row.appendImage(SimpleImage())
	row = row.appendImage(SecondImage())
	row = row.appendImage(ThirdImage())

	if row.numImages() != 3 {
		t.Error("Row did not have the correct number of images")
	}
}

func TestRow_NumPosts(t *testing.T) {
	row := Row{}
	row = row.appendImage(SimpleImage())
	row = row.appendImage(SecondImage())
	row = row.appendImage(ThirdImage())

	left, right := row.numPosts()

	if left != 0 || right != 2 {
		t.Errorf("Expected the number of starting posts to be 0 and the ending posts to be 2, but %d and %d was found", left, right)
	}
}
