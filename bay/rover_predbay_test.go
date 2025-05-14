package main

import (
	"fmt"
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
		"test/pic/foo3.jpg",
		"2024-05-21",
		"13:024:00",
		true,
		1,
		3,
		"East",
	}

	return img
}

func NoPostImage() Image {
	img := Image{
		"test/pic/foo4.jpg",
		"2024-07-21",
		"13:024:00",
		false,
		1,
		1,
		"East",
	}

	return img
}

func PostImage() Image {
	img := Image{
		"test/pic/foo4.jpg",
		"2024-07-21",
		"13:024:00",
		true,
		1,
		1,
		"East",
	}

	return img
}

func TestBay_PopLast_Single(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())

	_, newBay := bay.PopLast()

	if newBay.NumImages() != 0 {
		t.Errorf("Expected new bay to be empty but found %d images\n", newBay.NumImages())
	}

	if bay.NumImages() != 1 {
		t.Errorf("Expected old bay to have a single image but found %d\n", bay.NumImages())
	}
}

func TestBay_PopLast_Two(t *testing.T) {

	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())

	_, newBay := bay.PopLast()

	if newBay.NumImages() != 1 {
		t.Errorf("Expected new bay to have a single image but found %d images\n", newBay.NumImages())
	}

	if newBay.images[0] != SimpleImage() {
		t.Errorf("Wrong image remaining in the new bay\n")
	}

	if bay.NumImages() != 2 {
		t.Errorf("Expected old bay to have a single image but found %d\n", bay.NumImages())
	}

	if bay.images[1] != SecondImage() || bay.images[0] != SimpleImage() {
		t.Errorf("Wrong image remaining in the old bay\n")
	}
}

func TestBay_PopLast_DoublePop(t *testing.T) {

	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())

	_, middleBay := bay.PopLast()
	_, newBay := middleBay.PopLast()

	if middleBay.NumImages() != 1 {
		t.Errorf("Expected the intermediate bay to have 1 image but is has %d\n", middleBay.NumImages())
	}

	if bay.NumImages() != 2 {
		t.Errorf("Expected the original bay to have 2 images but it has %d\n", bay.NumImages())
	}

	if newBay.NumImages() != 0 {
		t.Errorf("Expected new bay to have no images but it has %d\n", newBay.NumImages())
	}
}

func TestBay_AppendImage_Empty(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())

	if len(bay.images) != 1 || bay.images[0] != SimpleImage() {
		t.Error("Image was not added to an empty bay")
	}
}

func TestBay_AppendImage(t *testing.T) {
	bay := Bay{}
	bay.images = append(bay.images, SimpleImage())

	bay = bay.AppendImage(SecondImage())

	if len(bay.images) != 2 || bay.images[0] != SimpleImage() || bay.images[1] != SecondImage() {
		t.Error("Image was not added to a bay with images")
	}
}

func TestBay_AppendImage_MultipleImages(t *testing.T) {
	left := Bay{}
	left = left.AppendImage(SecondImage())
	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(NoPostImage())

	expected := []Image{SecondImage(), SimpleImage(), SimpleImage(), NoPostImage()}

	if left.NumImages() != len(expected) {
		t.Errorf("Expected %d images but found %d\n", len(expected), left.NumImages())
	}

	for i := 0; i < len(expected); i++ {
		if left.images[i] != expected[i] {
			t.Errorf("At %d, found %s, expected %s\n", i, fmt.Sprint(left.images[i]), fmt.Sprint(expected[i]))
		}
	}
}

func TestBay_GiveToStartOf_Empties(t *testing.T) {
	left := Bay{}
	right := Bay{}

	left = left.AppendImage(SimpleImage())
	left, right = left.GiveToStartOf(&right)

	if len(left.images) != 0 {
		t.Error("Giving bay did not remove image")
	}

	if len(right.images) != 1 || right.images[0] != SimpleImage() {
		t.Error("Receiving bay did not add image")
	}
}

func TestBay_GiveToStartOf(t *testing.T) {
	left := Bay{}
	right := Bay{}

	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(ThirdImage())
	right = right.AppendImage(SecondImage())

	left, right = left.GiveToStartOf(&right)

	if len(left.images) != 1 || left.images[0] != SimpleImage() {
		t.Error("Giving bay does not have the correct images after giveToStartOf")
	}

	if len(right.images) != 2 || right.images[0] != ThirdImage() || right.images[1] != SecondImage() {
		t.Error("Receiving bay did not add image")
	}
}

func TestBay_GiveToStartOf_MultipleMove(t *testing.T) {
	left := Bay{}
	right := Bay{}
	left = left.AppendImage(SecondImage())
	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(SimpleImage())
	left = left.AppendImage(NoPostImage())

	start := []Image{SecondImage(), SimpleImage(), SimpleImage(), NoPostImage()}

	if left.NumImages() != len(start) {
		t.Errorf("Images not properly appended to giving bay to start with: %d\n", len(left.images))
	}

	for i := 0; i < len(start); i++ {
		if left.images[i] != start[i] {
			t.Errorf("Expected %s but found %s\n", fmt.Sprint(left.images[i]), fmt.Sprint(start[i]))
		}
	}

	left, right = left.GiveToStartOf(&right)

	if left.NumImages() != 1 && left.images[0] != SecondImage() {
		t.Errorf("Giving bay does not have the single post image left: (%d) %s\n", left.NumImages(), fmt.Sprint(left.images))
	}

	if right.NumImages() != 3 {
		t.Errorf("Not enough image were transfered to the receiving bay\n")
	}

	if right.NumImages() == 3 && right.images[2] != NoPostImage() {
		t.Errorf("Receiving bay does not have the images in the correct order\n")
	}
}

func TestBay_HasImages_NonEmpty(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())

	if !bay.HasImages() {
		t.Error("Bay did not have images")
	}
}

func TestBay_HasImages_Empty(t *testing.T) {
	bay := Bay{}

	if bay.HasImages() {
		t.Error("Empty bay reported to have images")
	}
}

func TestBay_TakeFromStartOf(t *testing.T) {

	left := Bay{}
	right := Bay{}

	left = left.AppendImage(SimpleImage())
	right = right.AppendImage(ThirdImage())
	right = right.AppendImage(SecondImage())

	left, right = left.TakeFromStartOf(&right)

	if len(left.images) != 2 || left.images[1] != ThirdImage() {
		t.Error("The receiving bay did not add the image")
	}

	if len(right.images) != 1 || right.images[0] != SecondImage() {
		t.Error("The giving bay did not have the correct number of images")
	}
}

func TestBay_NumEmpty(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(ThirdImage())

	if bay.NumEmpty() != 1 {
		t.Error("Bay did not have the correct number of non-post images")
	}
}

func TestBay_NumImages(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(ThirdImage())

	if bay.NumImages() != 3 {
		t.Error("Bay did not have the correct number of images")
	}
}

func TestBay_NumPosts(t *testing.T) {
	bay := Bay{}
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(ThirdImage())

	start, end := bay.NumPosts()

	if start+end != 2 {
		t.Error("Bay did not have the correct number of images with posts")
	}
}

func TestBay_MiddlePosts(t *testing.T) {
	answer := 1
	bay := Bay{}
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())

	middle := bay.MiddlePosts()

	if middle != answer {
		t.Errorf("The number of middle posts was expected to be %d but %d was found", answer, middle)
	}
}

func TestRowAssignment_GenerateAssignments(t *testing.T) {
	first := Bay{}
	second := Bay{}
	third := Bay{}

	//add two images per bay because GenerateAssignments won't allow for empty bays
	first = first.AppendImage(SimpleImage())
	first = first.AppendImage(SimpleImage())
	second = second.AppendImage(SecondImage())
	second = second.AppendImage(SecondImage())
	third = third.AppendImage(ThirdImage())
	third = third.AppendImage(ThirdImage())

	row := RowAssignment{}
	row.rowNum = 1
	row.bays = append(row.bays, first)
	row.bays = append(row.bays, second)
	row.bays = append(row.bays, third)

	results := row.generateAssignments()

	if len(results) != 4 {
		t.Error("Expected 4 new assignments, got ", len(results))
	}
}

func TestRowAssignment_ReplaceBays(t *testing.T) {

	first := Bay{}
	second := Bay{}
	third := Bay{}

	first = first.AppendImage(SimpleImage())
	second = second.AppendImage(SecondImage())
	third = third.AppendImage(ThirdImage())

	row := RowAssignment{}
	row.rowNum = 1
	row.bays = append(row.bays, first)
	row.bays = append(row.bays, second)
	row.bays = append(row.bays, third)

	newSecond := second.AppendImage(SecondImage())
	newThird := third.AppendImage(ThirdImage())

	row = row.ReplaceBays(1, newSecond, 2, newThird)

	if len(row.bays[1].images) != 2 {
		t.Error("new second bay has the incorrect number of images")
	}

	if len(row.bays[2].images) != 2 {
		t.Error("new third bay has the incorrect number of images")
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

func TestModel_LogLikelihood(t *testing.T) {

	//check bay in each row should contribute -1, but last bay in each row will be a bit more than -1
	answer := (-1.4959226032237258 - 0.3160815469734788) * NUM_BAYS * 3
	row := NewRowAssignment(1, false)
	model := NewDPModel(3.0, .9)

	//add images to each bay
	for i := 0; i < len(row.bays); i++ {
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())

		row.bays[i] = row.bays[i].AppendImage(SimpleImage())
		row.bays[i] = row.bays[i].AppendImage(SimpleImage())
		row.bays[i] = row.bays[i].AppendImage(SimpleImage())

		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
	}

	like := model.RowLogLikelihood(&row)
	diff := math.Abs(like - answer)

	if diff > .001 {
		t.Errorf("The likelihood should be around %f but is %.4f differing by %f", answer, like, diff)
	}
}

func TestModel_MaxSectionAssignment(t *testing.T) {
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	part := model.maxSectionAssignment(&bay)
	answers := [3]int{0, 3, 6}

	for i, end := range answers {
		if part[i] != end {
			t.Errorf("Expected partition %d to end at %d but ended at %d (%s)\n", i, end, part[i], fmt.Sprint(part))
		}
	}
}

func TestModel_MaxSectionNoise(t *testing.T) {
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())

	part := model.maxSectionAssignment(&bay)
	answers := [3]int{0, 3, 6}

	for i, end := range answers {
		if part[i] != end {
			t.Errorf("Expected partition %d to end at %d but ended at %d (%s)\n", i, end, part[i], fmt.Sprint(part))
		}
	}
}

func TestModel_MaxSectionMoreNoise(t *testing.T) {
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	part := model.maxSectionAssignment(&bay)
	answers := [3]int{0, 3, 6}

	for i, end := range answers {
		if part[i] != end {
			t.Errorf("Expected partition %d to end at %d but ended at %d (%s)\n", i, end, part[i], fmt.Sprint(part))
		}
	}
}

func TestModel_MaxSectionYetMoreNoise(t *testing.T) {
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage()) //1
	bay = bay.AppendImage(SecondImage()) //2

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage()) //4
	bay = bay.AppendImage(SecondImage()) //5

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SecondImage()) //7
	bay = bay.AppendImage(SimpleImage()) //8

	part := model.maxSectionAssignment(&bay)
	answers := [3]int{0, 3, 5}

	for i, end := range answers {
		if part[i] != end {
			t.Errorf("Expected partition %d to end at %d but ended at %d (%s)\n", i, end, part[i], fmt.Sprint(part))
		}
	}
}

func TestModel_MaxSectionDiffNoise(t *testing.T) {
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage()) //1
	bay = bay.AppendImage(SecondImage()) //2

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage()) //4
	bay = bay.AppendImage(SimpleImage()) //5

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SecondImage()) //7
	bay = bay.AppendImage(SimpleImage()) //8

	part := model.maxSectionAssignment(&bay)
	answers := [3]int{0, 3, 6}

	for i, end := range answers {
		if part[i] != end {
			t.Errorf("Expected partition %d to end at %d but ended at %d (%s)\n", i, end, part[i], fmt.Sprint(part))
		}
	}
}
func TestModel_backwardsPass(t *testing.T) {
	const LAST = 0

	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	//add images to the bay
	bay = bay.AppendImage(SecondImage()) //0
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage()) //3
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage()) //6
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())
	n := bay.NumImages()

	ANSWER := model.sectionLogLike(&bay, 0, 0, 3) + model.sectionLogLike(&bay, 1, 3, 6) + model.sectionLogLike(&bay, 2, 6, n)

	table := model.backwardsPass(&bay)

	if table[LAST][0] != ANSWER {
		t.Errorf("Probability of being in the starting state should be %f, but %f was found\n", ANSWER, table[LAST][0])
	}
}

func TestModel_sectionLikelihood(t *testing.T) {

	homoAnswer := -1.4959226032237258 - 0.3160815469734788
	hetroAnswer := -1.4959226032237258 - 1.4146938356415888

	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	firstLike := model.sectionLogLike(&bay, 0, 0, 3)
	secondLike := model.sectionLogLike(&bay, 1, 3, 6)

	if math.Abs(homoAnswer-firstLike) > 0.001 {
		t.Errorf("For section 0, the expected likelihood is %.4f but %.4f was found\n", homoAnswer, firstLike)
	}

	if math.Abs(hetroAnswer-secondLike) > 0.001 {
		t.Errorf("For section 1, the expected likelihood is %.4f but %.4f was found\n", hetroAnswer, secondLike)
	}
}

func TestModel_bayLogLikelihood(t *testing.T) {
	answer := (-1.4959226032237258 - 0.3160815469734788) * 3
	model := NewDPModel(3.0, .9)
	bay := Bay{1, make([]Image, 0)}

	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())
	bay = bay.AppendImage(SimpleImage())

	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())
	bay = bay.AppendImage(SecondImage())

	part := []int{0, 3, 6}

	like := model.bayLogLikelihood(&bay, part)

	if math.Abs(like-answer) > .001 {
		t.Errorf("Expected the likelihood to be %.4f but %.4f was found\n", answer, like)
	}
}

func TestModel_ExpectedModel(t *testing.T) {
	row := NewRowAssignment(1, false)
	model := NewDPModel(3.0, .9)

	//add images to each bay
	for i := 0; i < len(row.bays); i++ {
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())

		row.bays[i] = row.bays[i].AppendImage(SimpleImage())
		row.bays[i] = row.bays[i].AppendImage(SimpleImage())
		row.bays[i] = row.bays[i].AppendImage(SimpleImage())

		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
		row.bays[i] = row.bays[i].AppendImage(SecondImage())
	}

	data := make([]CameraAssignment, 1)
	data[0] = make([]RowAssignment, 1)
	data[0][0] = row

	model.ExpectedModel(data)

	for i, lambda := range model.count {
		if math.Abs(lambda-3.0) > .0001 {
			t.Errorf("Expected Poisson parameter to be 3.0 but it was %f for section %d\n", lambda, i)
		}
	}

	expectedProb := []float64{0.0, 1.0, 0.0}

	for i, prob := range model.composition {
		if math.Abs(prob-expectedProb[i]) > .0001 {
			t.Errorf("Expected a non-post probability of %.4f but %.4f was found for section %d\n", expectedProb[i], prob, i)
		}
	}
}
