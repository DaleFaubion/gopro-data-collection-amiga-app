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
		"test/pic/foo2.jpg",
		"2024-05-21",
		"13:024:00",
		true,
		1,
		3,
		"East",
	}

	return img
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

/*func TestMakeInitialGroups(t *testing.T) {
	numImages := 21 * 3 * 3
	perBayNum := 3
	images := []Image{}

	for i := 0; i < numImages; i++ {
		switch i % 3 {
		case 0:
			images = append(images, SimpleImage())
		case 1:
			images = append(images, SecondImage())
		case 2:
			images = append(images, ThirdImage())
		}
	}

	assignments := makeInitialGroups(images)

	if len(assignments) != 4 {
		t.Errorf("Number of camera assignments should be 4 but found %d", len(assignments))
	}

	total := 0

	// count up all the images for all the cameras and rows
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < NUM_BAYS; i++ {
			total += assignments[c][0].bays[i].NumImages()
			total += assignments[c][1].bays[i].NumImages()
		}
	}

	if total != numImages {
		t.Errorf("Expected %d images but found %d", numImages, total)
	}

	// ensure that the there are the correct number of rows and bays per each camera TODO
	for c := 0; c < CAMERAS; c++ {

		//check that there are enough rows
		if len(assignments[c]) != NUM_ROWS {
			t.Errorf("Camera %d has %d rows\n", c, len(assignments[c]))
		}

		// in each row check that there are enough bays
		for r, row := range assignments[c] {

			if len(row.bays) != NUM_BAYS {
				t.Errorf("Row %d has %d bays\n", r, len(row.bays))
			}
		}
	}

	// check all but the last camera for images
	for i := 0; i < CAMERAS-1; i++ {
		rows := assignments[i]
		row := rows[0]

		//camera 1 has a different orientation so the images end up in a different row
		if i == 0 {
			row = rows[1]
		}

		for j, bay := range row.bays {

			expected := perBayNum - 1

			if j%2 == 1 {
				expected = perBayNum + 1
			}

			if bay.NumImages() != expected {
				t.Errorf("camera %d, bay %d should have %d images but actually has %d", i, j, expected, bay.NumImages())
			}
		}
	}
}*/

// NOTE: this function depends upon external files!
func TestLoadPostData(t *testing.T) {
	postData := loadPostData("../pred/post-pred/posts-2020-07-20.csv")

	if len(postData) != 3688 {
		t.Errorf("File should have 3688 images but %d found\n", len(postData))
	}

	posts := 0

	for _, post := range postData {
		if post {
			posts++
		}
	}

	if posts == 0 {
		t.Errorf("Some posts should have been loaded")
	}
}

// NOTE: this function depends upon external files!
func TestLoadRowData(t *testing.T) {
	postData := loadPostData("../pred/post-pred/all-2023-posts.csv")
	rowData := loadRowData(postData, "../pred/row-pred-old/row-pred-2023-07-03.csv")

	if len(postData) != 99770 {
		t.Errorf("Post file should have 99770 images but %d found\n", len(postData))
	}

	if len(rowData) != 9458 {
		t.Errorf("Row file should have 9458 images but %d found\n", len(rowData))
	}

	//check that the correct number of post images: 6608 (maybe 6658?)
	posts := 0

	for _, img := range rowData {
		if img.hasPost {
			posts++
		}
	}

	if posts != 6608 {
		t.Errorf("Expected 6658 images with posts but found %d\n", posts)
		t.Error()
	}
}

//TODO moved the logic to skip to edge rows to makeInitialGroups
/*func TestLoadSkipRowData(t *testing.T) {
	postData := loadPostData("../pred/post-data/all-2023-posts.csv")
	rowData := loadRowData(postData, "../test-data/row-pred.csv")

	if len(rowData) != 0 {
		t.Errorf("Row file should have 0 in-bounds images but %d found\n", len(rowData))
		t.Error("path", rowData[0].path, "date", rowData[0].date, "time", rowData[0].time, "row", rowData[0].row, "camera", rowData[0].cameraNum, "dir", rowData[0].direction)
		//t.Errorf("Row number %d\n", rowData[0].row)
	}
}*/

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
