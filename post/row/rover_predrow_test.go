package main

import (
	"math"
	"testing"
)

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
	row = row.AppendImage(SimpleImage())

	if len(row.images) != 1 || row.images[0] != SimpleImage() {
		t.Error("Image was not added to an empty row")
	}
}

func TestRow_AppendImage(t *testing.T) {
	row := Row{}
	row.images = append(row.images, SimpleImage())

	row = row.AppendImage(SecondImage())

	if len(row.images) != 2 || row.images[0] != SimpleImage() || row.images[1] != SecondImage() {
		t.Error("Image was not added to a row with images")
	}
}

func TestRow_GiveToStartOf_Empties(t *testing.T) {
	left := Row{}
	right := Row{}

	left = left.AppendImage(SimpleImage())
	left, right = left.GiveToStartOf(&right)

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

	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(ThirdImage())
	right = right.AppendImage(SecondImage())

	left, right = left.GiveToStartOf(&right)

	if len(left.images) != 1 || left.images[0] != SimpleImage() {
		t.Error("Giving row does not have the correct images after giveToStartOf")
	}

	if len(right.images) != 2 || right.images[0] != ThirdImage() || right.images[1] != SecondImage() {
		t.Error("Receiving row did not add image")
	}
}

func TestRow_HasImages_NonEmpty(t *testing.T) {
	row := Row{}
	row = row.AppendImage(SimpleImage())

	if !row.HasImages() {
		t.Error("Row did not have images")
	}
}

func TestRow_HasImages_Empty(t *testing.T) {
	row := Row{}

	if row.HasImages() {
		t.Error("Empty row reported to have images")
	}
}

func TestRow_TakeFromStartOf(t *testing.T) {

	left := Row{}
	right := Row{}

	left = left.AppendImage(SimpleImage())
	right = right.AppendImage(ThirdImage())
	right = right.AppendImage(SecondImage())

	left, right = left.TakeFromStartOf(&right)

	if len(left.images) != 2 || left.images[1] != ThirdImage() {
		t.Error("The receiving row did not add the image")
	}

	if len(right.images) != 1 || right.images[0] != SecondImage() {
		t.Error("The giving row did not have the correct number of images")
	}
}

func TestRow_NumEmpty(t *testing.T) {
	row := Row{}
	row = row.AppendImage(SimpleImage())
	row = row.AppendImage(SecondImage())
	row = row.AppendImage(ThirdImage())

	if row.NumEmpty() != 1 {
		t.Error("Row did not have the correct number of non-post images")
	}
}

func TestRow_NumImages(t *testing.T) {
	row := Row{}
	row = row.AppendImage(SimpleImage())
	row = row.AppendImage(SecondImage())
	row = row.AppendImage(ThirdImage())

	if row.NumImages() != 3 {
		t.Error("Row did not have the correct number of images")
	}
}

func TestRow_NumPosts(t *testing.T) {
	row := Row{}
	row = row.AppendImage(SimpleImage())
	row = row.AppendImage(SecondImage())
	row = row.AppendImage(ThirdImage())

	if row.NumPosts() != 2 {
		t.Error("Row did not have the correct number of images with posts")
	}
}

func Test_LogProb_1(t *testing.T) {
	prob := PoissonLogProb(1, 1)

	if prob != -1.0 {
		t.Errorf("Log Poi. prob of 1 with lambda = 1 should be -1 but %f was calculated", prob)
	}
}

func Test_LogProb_2(t *testing.T) {
	const answer = 1.3068528194400546
	prob := PoissonLogProb(2, 1)

	if math.Abs(prob+answer) > 0.00001 {
		t.Errorf("Log Poi. prob of 2 with lambda = 1 should be -%f but %f was calculated", answer, prob)
	}
}

func Test_LogProb_lambda3_2(t *testing.T) {
	const answer = 1.4959226032237258
	prob := PoissonLogProb(3, 2)

	if math.Abs(prob+answer) > 0.00001 {
		t.Errorf("Log Poi. prob of 1 with lambda = 1 should be -%f but %f was calculated", answer, prob)
	}
}
