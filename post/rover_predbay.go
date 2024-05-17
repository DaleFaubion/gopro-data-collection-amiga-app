package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"math"
	"os"
	"strconv"
)

const NUM_ROWS = 21
const NUM_BAYS = 21

// Image a single image
type Image struct {
	path    string
	time    string
	hasPost bool
	row     int
}

// Bay an assignment of images to a particular bay in a single row
type Bay struct {
	bayNum int
	images []Image
}

// AppendImage appends a new image to the bay, returns a new bay
func (bay *Bay) AppendImage(image Image) Bay {
	newImages := append(bay.images, image)
	return Bay{bay.bayNum, newImages}
}

// PrependImage prepends a new image to the bay, returns a new bay
func (bay *Bay) PrependImage(image Image) Bay {
	singleton := []Image{image}
	newImages := append(singleton, bay.images...)
	return Bay{bay.bayNum, newImages}
}

// PopFirst removes and returns the first image, returns a new bay
func (bay *Bay) PopFirst() (Image, Bay) {
	first := bay.images[0]
	rest := bay.images[1:]
	result := Bay{bay.bayNum, rest}
	return first, result
}

// PopLast removes and returns the last image, returns a new bay
func (bay *Bay) PopLast() (Image, Bay) {
	last := bay.images[len(bay.images)-1]
	rest := bay.images[:len(bay.images)-1]
	result := Bay{bay.bayNum, rest}
	return last, result
}

// GiveToStartOf removes an image from the end of this bay and gives it to the start of the other bay, returns
// two new bays
func (bay *Bay) GiveToStartOf(other *Bay) (Bay, Bay) {
	toGive, newLeft := bay.PopLast()
	newRight := other.PrependImage(toGive)
	return newLeft, newRight
}

// TakeFromStartOf takes the first image from the other bay and appends it to this one, returns two new bays
func (bay *Bay) TakeFromStartOf(other *Bay) (Bay, Bay) {
	toGive, newRight := other.PopFirst()
	newLeft := bay.AppendImage(toGive)
	return newLeft, newRight
}

// HasImages returns true if there are images in the bay
func (bay *Bay) HasImages() bool {
	return len(bay.images) > 0
}

// NumPosts returns the number of images that contain a post in the bay
func (bay *Bay) NumPosts() int {
	count := 0

	for _, image := range bay.images {
		if image.hasPost {
			count++
		}
	}

	return count
}

// NumEmpty returns the number of images that do not contain a post in the bay
func (bay *Bay) NumEmpty() int {
	return bay.NumImages() - bay.NumPosts()
}

// NumImages returns the number of images in the bay
func (bay *Bay) NumImages() int {
	return len(bay.images)
}

// RowAssignment the assignment of images to bays in a single row
type RowAssignment struct {
	rowNum int
	bays   []Bay
}

// ReplaceBays update the assignment, with a bay, creates a new assignment
func (row *RowAssignment) ReplaceBays(firstIdx int, left Bay, secondIdx int, right Bay) RowAssignment {
	newBays := make([]Bay, len(row.bays))
	copy(newBays, row.bays)
	newBays[firstIdx] = left
	newBays[secondIdx] = right
	return RowAssignment{row.rowNum, newBays}
}

//GenerateAssignments creates new assignments by moving single images to adjacent bays
func (row *RowAssignment) GenerateAssignments() []RowAssignment {
	var results []RowAssignment

	// generate two new assignments per each pair of bays, i.e. move an image from left to right and
	// from right to left
	for i := 0; i < len(row.bays)-1; i++ {
		left := row.bays[i]
		right := row.bays[i+1]

		toLeftLeft, toLeftRight := left.TakeFromStartOf(&right)
		first := row.ReplaceBays(i, toLeftLeft, i+1, toLeftRight)
		results = append(results, first)

		toRightLeft, toRightRight := left.GiveToStartOf(&right)
		second := row.ReplaceBays(i, toRightLeft, i+1, toRightRight)
		results = append(results, second)
	}

	return results
}

type Model struct {
	imageLambda float64
	postLambda  float64
}

// RowLogLikelihood computes the likelihood of the row assignment
func (model *Model) RowLogLikelihood(row *RowAssignment) float64 {

	like := 0.0

	for _, bay := range row.bays {

		// compute the probability of the regular images
		reg := PoissonLogProb(model.imageLambda, bay.NumEmpty())

		// compute the probability of the post images
		post := PoissonLogProb(model.postLambda, bay.NumPosts())

		like += reg + post
	}

	return like
}

// LogLikelihood computes the score for the whole assignment
func (model *Model) LogLikelihood(rows []RowAssignment) float64 {
	like := 0.0

	for _, row := range rows {
		like += model.RowLogLikelihood(&row)
	}

	return like
}

// PoissonLogProb computes the log probability of a count under a Poisson distribution
func PoissonLogProb(lambda float64, count int) float64 {
	if count <= 0 {
		// use a very small probability instead of zero
		return math.Log(0.00000000001)
	} else {
		// the numerator is lambda^k e^-lambda i.e. in log space: k ln lambda - lambda
		num := float64(count)*math.Log(lambda) - lambda
		denom := 0

		// the denominator is the sum of 1 to k i.e. the log of the factorial of the count
		for i := 1; i <= count; i++ {
			denom += i
		}

		// in log space, the numerator over the denominator is simply subtraction
		return num - float64(denom)
	}
}

// LoadPostData loads the post predictions from a given CSV file
func LoadPostdata(path string) map[string]bool {
	const pathIdx = 0
	const postIdx = 2
	const hasPost = 1

	data, fileErr := os.Open(path)

	//return nothing on error
	if fileErr != nil {
		return make(map[string]bool)
	}

	defer data.Close()

	reader := csv.NewReader(data)

	records, err := reader.ReadAll()

	// return nothing on error
	if err != nil {
		return make(map[string]bool)
	}

	results := make(map[string]bool)

	// build a map from path name to bool (has post or not)
	for _, record := range records {
		path := record[pathIdx]
		post, postErr := strconv.Atoi(record[postIdx])

		if postErr != nil {
			results[path] = post == hasPost
		}
	}

	return results
}

// LoadRowData reads the CSV file and constructs an array of images
func LoadRowData(posts map[string]bool, path string) []Image {
	const pathIdx = 0
	const timeIdx = 1
	const rowIdx = 3

	data, fileErr := os.Open(path)

	if fileErr != nil {
		return []Image{}
	}

	defer data.Close()
	reader := csv.NewReader(data)

	records, err := reader.ReadAll()

	if err != nil {
		return []Image{}
	}

	results := make([]Image, len(records))
	for i, record := range records {
		row, _ := strconv.Atoi(record[rowIdx])
		path := record[pathIdx]
		newImage := Image{path, record[timeIdx], posts[path], row}
		results[i] = newImage
	}

	return results
}

// MakeInitialGroups creates an assignment for each row based on the data and the row/bay constraints
func MakeInitialGroups(images []Image) []RowAssignment {

	rows := make([][]Image, NUM_ROWS)

	// put all the images into their row array
	for _, image := range images {
		rowIdx := image.row - 1
		rows[rowIdx] = append(rows[rowIdx], image)
	}

	results := make([]RowAssignment, NUM_ROWS)

	// make bays for all the rows
	for i := 0; i < len(results); i++ {
		results[i].rowNum = i + 1

		for j := 0; j < NUM_BAYS; j++ {
			results[i].bays = append(results[i].bays, Bay{j + 1, make([]Image, 0)})
		}
	}

	// group up all the images into row assignments
	// for each row, evenly distribute images to each bay
	for i := 0; i < len(results); i++ {
		step := int(math.Round(float64(len(rows[i])) / NUM_BAYS))

		for j := 0; j < len(rows[i]); j++ {
			bayIdx := j / step
			results[i].bays[bayIdx].AppendImage(rows[i][j])
		}
	}

	return results
}

// EM runs the expectation maximization algorithm to find the best row assignment
func EM(model *Model, init []RowAssignment, rounds int) []RowAssignment {

	results := init

	// for a fixed number of iterations, run the EM algo
	for i := 0; i < rounds; i++ {

		// for each row, find the best assignment
		for j := 0; j < len(results); j++ {
			results[j] = MaxRow(model, results[j])
		}

		// estimate the model parameters
		ExpectedModel(model, results)
	}

	return results
}

// MaxRow find the row that maximizes the likelihood under the current model
func MaxRow(model *Model, row RowAssignment) RowAssignment {

	done := false
	best := row
	bestScore := model.RowLogLikelihood(&best)

	// until there is no improvement, greedily try different assignments
	for !done {

		done = true

		// generate a collection of assignments
		candidates := best.GenerateAssignments()

		// evaluate all the assignments and pick the best
		for _, candidate := range candidates {

			score := model.RowLogLikelihood(&candidate)

			//if it is an improvement, remember it and continue
			if score > bestScore {
				best = candidate
				bestScore = score
				done = false
			}
		}

	}

	return best
}

// ExpectedModel updates the models parameters based on the current assignment
func ExpectedModel(model *Model, init []RowAssignment) {

	avgEmpty := 0.0
	avgPost := 0.0
	total := 0

	// average the number of empty images in all the bays
	for i := 0; i < len(init); i++ {
		for j := 0; j < len(init[i].bays); j++ {
			avgEmpty += float64(init[i].bays[j].NumEmpty())
			avgPost += float64(init[i].bays[j].NumPosts())
			total += 1
		}
	}

	//average the number of post images in all the bays
	model.imageLambda = avgEmpty / float64(total)
	model.postLambda = avgPost / float64(total)
}

func main() {

	rowFile := flag.String("row_file", "", "The path to the CSV file containing predicted rows")
	postFile := flag.String("post_file", "", "The path to the CSV file containing predicted posts")

	flag.Parse()

	fmt.Println(*rowFile)
	fmt.Println(*postFile)
}
