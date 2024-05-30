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

// NewCameraAssignment creates an empty assignment for all the rows, for a single camera
func NewCameraAssignment() CameraAssignment {
	results := make([]RowAssignment, NUM_ROWS)

	for i := 0; i < NUM_ROWS; i++ {
		results[i] = NewRowAssignment(i + 1)
	}

	return results
}

// NewVineyardAssignment creates a empty ent for all the rows and bays
func NewVineyardAssignment() []CameraAssignment {
	results := make([]CameraAssignment, CAMERAS)

	for i := 0; i < CAMERAS; i++ {
		results[i] = NewCameraAssignment()
	}

	return results
}

// loadPostData loads the post predictions from a given CSV file
func loadPostData(path string) map[string]bool {
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

// validRows returns true if the row number is within the bounds of the block i.e. a couple row 0 and 22 are actually
// of other blocks
func validRows(rowIdx int) bool {
	return rowIdx > 0 && rowIdx <= NUM_ROWS
}

// loadRowData reads the CSV file and constructs an array of images
func loadRowData(posts map[string]bool, path string) []Image {
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

	var results []Image

	for _, record := range records {
		row, _ := strconv.Atoi(record[rowIdx])

		if validRows(row) {
			imgPath := record[pathIdx]
			camera, _ := strconv.Atoi(record[cameraIdx])
			newImage := Image{imgPath, record[dateIdx], record[timeIdx], posts[imgPath], row, camera, record[dirIdx]}
			results = append(results, newImage)
		}
	}

	return results
}

// MakeInitialGroups creates an ent for each row based on the data and the row/bay constraints
func makeInitialGroups(images []Image) []CameraAssignment {

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

	// group up all the images into row ents
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

// ShowRows prints off the row ents
func showRows(rows []CameraAssignment) {

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
func writeBays(path string, bays []CameraAssignment) {
	const WEST = "West"

	// open the file
	file, err := os.Create(path)

	if err != nil {
		fmt.Printf("Cannot write to %s: %s\n", path, err)
		os.Exit(1)
	}

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

	writer.Flush()
	closeErr := file.Close()

	if closeErr != nil {
		fmt.Println("Error closing file: ", closeErr)
	}
}

func main() {

	// Set up the optional flags
	rounds := flag.Int("rounds", 500, "The number of rounds to apply EM")
	outFile := flag.String("out", "", "The path to the CSV file to write with the bay predictions")

	flag.Parse()

	if len(flag.Args()) < 2 {
		fmt.Printf("Usage: <row file> <post file>\n")
		os.Exit(1)
	}

	// get the position args
	rowFile := flag.Arg(0)
	postFile := flag.Arg(1)

	// Load the posts
	posts := loadPostData(postFile)

	if len(posts) == 0 {
		fmt.Printf("No posts found in %s\n", postFile)
		os.Exit(1)
	}

	// load the row information
	images := loadRowData(posts, rowFile)

	if len(images) == 0 {
		fmt.Printf("No images found in %s\n", rowFile)
		os.Exit(1)
	}

	// make an initial ent
	model := initialModel(images)

	// make an initial model
	start := makeInitialGroups(images)

	fmt.Println("Starting Groups")

	showRows(start)

	// use EM to correct the ents
	result := model.em(start, *rounds)

	fmt.Println("Results")

	// show the row ent
	showRows(result)

	// if an output file is given, write to it
	if *outFile != "" {
		writeBays(*outFile, result)
	}
}
