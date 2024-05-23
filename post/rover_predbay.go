package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"math"
	"os"
	"strconv"
)

// major types: Image, Bay, Assignment
// also Model

const NUM_ROWS = 21
const NUM_BAYS = 21
const CAMERAS = 4

type CameraAssignment = []RowAssignment

// Image a single image
type Image struct {
	path      string
	date      string
	time      string
	hasPost   bool
	row       int
	cameraNum int
	direction string
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

// NewRowAssignment creates a new row assignment
func NewRowAssignment(rowNum int) RowAssignment {
	assignment := RowAssignment{}
	assignment.rowNum = rowNum
	assignment.bays = make([]Bay, NUM_BAYS)
	return assignment
}

// NewCameraAssignment creates an assignment
func NewCameraAssignment() CameraAssignment {
	results := make([]RowAssignment, NUM_ROWS)

	for i := 0; i < NUM_ROWS; i++ {
		results[i] = NewRowAssignment(i + 1)
	}

	return results
}

// NewVineyardAssignment creates a empty assignment for all the rows and bays
func NewVineyardAssignment() []CameraAssignment {
	results := make([]CameraAssignment, CAMERAS)

	for i := 0; i < CAMERAS; i++ {
		results[i] = NewCameraAssignment()
	}

	return results
}

// ReplaceBays update the assignment, with a bay, creates a new assignment
func (row *RowAssignment) ReplaceBays(firstIdx int, left Bay, secondIdx int, right Bay) RowAssignment {
	newBays := make([]Bay, len(row.bays))
	copy(newBays, row.bays)
	newBays[firstIdx] = left
	newBays[secondIdx] = right
	return RowAssignment{row.rowNum, newBays}
}

// NumImages counts up the number of images in the row
func (row *RowAssignment) NumImages() int {
	total := 0

	for _, bay := range row.bays {
		total += bay.NumImages()
	}

	return total
}

//GenerateAssignments creates new assignments by moving single images to adjacent bays
func (row *RowAssignment) GenerateAssignments() []RowAssignment {
	var results []RowAssignment

	// generate two new assignments per each pair of bays, i.e. move an image from left to right and
	// from right to left
	for i := 0; i < len(row.bays)-1; i++ {
		left := row.bays[i]
		right := row.bays[i+1]

		if right.NumImages() > 1 {
			toLeftLeft, toLeftRight := left.TakeFromStartOf(&right)
			first := row.ReplaceBays(i, toLeftLeft, i+1, toLeftRight)
			results = append(results, first)
		}

		if left.NumImages() > 1 {
			toRightLeft, toRightRight := left.GiveToStartOf(&right)
			second := row.ReplaceBays(i, toRightLeft, i+1, toRightRight)
			results = append(results, second)
		}
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
func (model *Model) LogLikelihood(rows CameraAssignment) float64 {
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
		num := (float64(count) * math.Log(lambda)) - lambda
		denom := 0.0

		// the denominator is the sum of 1 to k i.e. the log of the factorial of the count
		for i := 1; i <= count; i++ {
			denom += math.Log(float64(i))
		}

		// in log space, the numerator over the denominator is simply subtraction
		return num - float64(denom)
	}
}

// LoadPostData loads the post predictions from a given CSV file
func LoadPostData(path string) map[string]bool {
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
	const dateIdx = 1
	const timeIdx = 2
	const rowIdx = 3
	const cameraIdx = 4
	const dirIdx = 5

	data, fileErr := os.Open(path)

	if fileErr != nil {
		fmt.Printf("Cannot open %s: %s\n", path, fileErr)
		return []Image{}
	}

	defer data.Close()
	reader := csv.NewReader(data)

	records, err := reader.ReadAll()

	if err != nil {
		fmt.Printf("Cannot create reader for %s: %s\n", path, err)
		return []Image{}
	}

	results := make([]Image, len(records))

	for i, record := range records {
		row, _ := strconv.Atoi(record[rowIdx])
		path := record[pathIdx]
		camera, _ := strconv.Atoi(record[cameraIdx])
		newImage := Image{path, record[dateIdx], record[timeIdx], posts[path], row, camera, record[dirIdx]}
		results[i] = newImage
	}

	return results
}

// MakeInitialGroups creates an assignment for each row based on the data and the row/bay constraints
func MakeInitialGroups(images []Image) []CameraAssignment {

	// make a data structure of camera, row, and then bay
	rows := make([][][]Image, CAMERAS)

	for i := range rows {
		rows[i] = make([][]Image, NUM_ROWS)
	}

	// put all the images into their row array
	for _, image := range images {
		rowIdx := image.row - 1
		camera := image.cameraNum - 1

		if rowIdx < NUM_ROWS {
			rows[camera][rowIdx] = append(rows[camera][rowIdx], image)
		}
	}

	results := NewVineyardAssignment()

	// group up all the images into row assignments
	// for each row, evenly distribute images to each bay
	for c := 0; c < CAMERAS; c++ {

		for i := 0; i < len(results[c]); i++ {

			// put every "step" size chunk of images into a new bag
			step := int(math.Ceil(float64(len(rows[c][i])) / NUM_BAYS))

			// if there are images for this camera/row add them to the output
			if step > 0 {

				for j := 0; j < len(rows[c][i]); j++ {

					bayIdx := j / step

					row := results[c][i]
					row.bays[bayIdx] = row.bays[bayIdx].AppendImage(rows[c][i][j])
				}
			}
		}
	}

	return results
}

// InitialModel creates an initial model based on the
func InitialModel(images []Image) Model {

	// create a set of parameters per row
	emptyCounts := 0.0
	postCounts := 0.0
	denom := float64(NUM_ROWS * NUM_BAYS)

	// for each image, increment the counts
	for _, image := range images {
		if image.hasPost {
			postCounts += 1
		} else {
			emptyCounts += 1
		}
	}

	// normalize
	return Model{emptyCounts / denom, postCounts / denom}
}

// EM runs the expectation maximization algorithm to find the best row assignment
func EM(model *Model, init []CameraAssignment, rounds int) []CameraAssignment {

	results := init

	// for a fixed number of iterations, run the EM algo
	for i := 0; i < rounds; i++ {

		for j := 0; j < CAMERAS; j++ {
			// for each row, find the best assignment
			for k := 0; k < len(results); k++ {
				results[j][k] = MaxRow(model, results[j][k])
			}
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
func ExpectedModel(model *Model, init []CameraAssignment) {

	avgEmpty := 0.0
	avgPost := 0.0
	total := 0

	// average the number of empty images in all the bays and cameras
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < len(init[c]); i++ {
			for j := 0; j < len(init[c][i].bays); j++ {
				avgEmpty += float64(init[c][i].bays[j].NumEmpty())
				avgPost += float64(init[c][i].bays[j].NumPosts())
				total += 1
			}
		}
	}

	//average the number of post images in all the bays
	model.imageLambda = avgEmpty / float64(total)
	model.postLambda = avgPost / float64(total)
}

// ShowRows prints off the row assignments
func ShowRows(rows []CameraAssignment) {

	for c := 0; c < CAMERAS; c++ {

		fmt.Printf("For camera %d\n\n", c+1)

		// print off each row
		for i, row := range rows[c] {
			fmt.Printf("%2d | ", i)

			// print off all the bays
			for _, bay := range row.bays {
				fmt.Printf("%4d | ", bay.NumImages())
			}

			fmt.Println()
		}

		fmt.Println()
	}
}

// WriteBays write out the pay predictions to the given file path
func WriteBays(path string, bays []CameraAssignment) {
	const WEST = "West"

	// open the file
	file, err := os.Create(path)

	if err != nil {
		fmt.Printf("Cannot write to %s: %s\n", path, err)
		os.Exit(1)
	}

	defer file.Close()

	// create the writer
	writer := csv.NewWriter(file)

	// write all the bay predictions
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < len(bays[c]); i++ {
			for j := 0; j < len(bays[c][i].bays); j++ {
				for k := 0; k < len(bays[c][i].bays[j].images); k++ {

					westDir := 0
					img := bays[c][i].bays[j].images[k]

					if img.direction == WEST {
						westDir = 1
					}

					row := []string{img.path, img.date, img.time, fmt.Sprint(i), fmt.Sprint(j), fmt.Sprint(westDir)}
					writer.Write(row)
				}
			}
		}
	}
}

func main() {

	// Set up the optional flags
	rounds := flag.Int("rounds", 5, "The number of rounds to apply EM")
	outFile := flag.String("out_file", "", "The path to the CSV file to write with the bay predictions")

	flag.Parse()

	if len(flag.Args()) < 2 {
		fmt.Printf("Usage: <row file> <post file> [out file]\n")
		os.Exit(1)
	}

	// get the position args
	rowFile := flag.Arg(0)
	postFile := flag.Arg(1)

	// Load the posts
	posts := LoadPostData(postFile)

	if len(posts) == 0 {
		fmt.Printf("No posts found in %s\n", postFile)
		os.Exit(1)
	}

	// load the row information
	images := LoadRowData(posts, rowFile)

	if len(images) == 0 {
		fmt.Printf("No images found in %s\n", rowFile)
		os.Exit(1)
	}

	// make an initial assignment
	model := InitialModel(images)

	// make an initial model
	start := MakeInitialGroups(images)

	fmt.Println("Starting Groups")

	ShowRows(start)

	// use EM to correct the assignments
	result := EM(&model, start, *rounds)

	fmt.Println("Results")

	// show the row assignment
	ShowRows(result)

	// if an output file is given, write to it
	if *outFile != "" {
		WriteBays(*outFile, result)
	}
}
