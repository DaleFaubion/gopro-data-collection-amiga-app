package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
)

const NUM_ROWS = 21
const NUM_BAYS = 21
const CAMERAS = 4
const CAMERA_SPLIT = 2
const WEST = "West"
const EAST = "East"

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

		row := i + 1

		// since the goes south on odd rows and north on even rows, flip the bay ordering on even rows
		reverseBays := row%2 == 0

		results[i] = NewRowAssignment(i+1, reverseBays)
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
	const postIdx = 3
	const hasPost = "1"

	data, fileErr := os.Open(path)

	//return nothing on error
	if fileErr != nil {
		fmt.Println("Cannot open posts file: ", path, " Error: ", fileErr)
		os.Exit(1)
	}

	defer data.Close()

	reader := csv.NewReader(data)

	records, err := reader.ReadAll()

	// return nothing on error
	if err != nil {
		fmt.Println("Cannot parse posts file: ", path, "Error: ", err)
		os.Exit(1)
	}

	results := make(map[string]bool)

	// build a map from path name to bool (has post or not)
	for _, record := range records {
		imgPath := record[pathIdx]
		results[imgPath] = record[postIdx] == hasPost
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

		imgPath := record[pathIdx]
		camera, _ := strconv.Atoi(record[cameraIdx])
		newImage := Image{imgPath, record[dateIdx], record[timeIdx], posts[imgPath], row, camera, record[dirIdx]}
		results = append(results, newImage)
	}

	return results
}

func isLeftCamera(cameraIdx int) bool {
	return cameraIdx == 1 || cameraIdx == 2
}

// MakeInitialGroups creates an ent for each row based on the data and the row/bay constraints
func makeInitialGroups(images []Image) []CameraAssignment {

	const MAX_BAY = NUM_BAYS - 1

	// make a data structure of camera, row, and then bay
	rows := make([][][]Image, CAMERAS)

	for i := range rows {
		rows[i] = make([][]Image, NUM_ROWS)
	}

	// put all the images into their row array
	for _, image := range images {
		rowIdx := image.row - 1
		camera := image.cameraNum - 1

		// unpack images into their own rows based on orientation
		if image.direction == WEST {
			//the left cameras are only on odd rows, move this image to the otherwise empty next even row
			if isLeftCamera(image.cameraNum) {
				rowIdx++
			} else {
				rowIdx--
			}
		}

		if 0 <= rowIdx && rowIdx < NUM_ROWS {
			rows[camera][rowIdx] = append(rows[camera][rowIdx], image)
		}
	}

	results := NewVineyardAssignment()

	// group up all the images into row assignments
	// for each row, evenly distribute images to each bay
	for c := 0; c < CAMERAS; c++ {

		for i := 0; i < len(results[c]); i++ {

			rowImages := rows[c][i]

			//by adding "step" amount, the extra images (remainder) will be evenly spread out across bays
			step := float64(NUM_BAYS) / float64(len(rowImages))
			index := 0.0

			for j := 0; j < len(rowImages); j++ {

				index += step

				//round down to the integer index
				bayIdx := int(math.Floor(index))

				//put extras on the end and/or avoid an extra bay
				if bayIdx > MAX_BAY {
					bayIdx = MAX_BAY
				}

				row := results[c][i]
				row.bays[bayIdx] = row.bays[bayIdx].AppendImage(rowImages[j])
			}

			//sort the images
			sort.Slice(rowImages, func(i, j int) bool {
				return rowImages[i].time < rowImages[j].time
			})
		}
	}

	return results
}

// ShowRows prints off the row ents
func showRows(rows []CameraAssignment) {

	for c := 0; c < CAMERAS; c++ {

		fmt.Printf("For camera %d\n\n", c+1)

		//print off the header
		fmt.Printf("    |")

		for i := 1; i <= NUM_BAYS; i++ {
			fmt.Printf("%5d    |", i)
		}
		fmt.Println()

		// print off each row
		for i, row := range rows[c] {
			realRow := calcRow(c, i)

			dir := "E"
			if calcDirection(c, i) == WEST {
				dir = "W"
			}

			fmt.Printf("%2d %s|", realRow, dir)

			for i := 0; i < len(row.bays); i++ {

				index := i

				if dir == "W" {
					index = len(row.bays) - 1 - i
				}
				bay := row.bays[index]
				start, end := bay.NumPosts()
				fmt.Printf("%2d+%2d+%2d |", start, bay.NumEmpty(), end)
			}
			fmt.Println()
		}

		fmt.Println()
	}
}

// calcRow determines the actual row based on the camera and assigned row
// row - is the row index i.e. starts at zero
func calcRow(camera int, row int) int {
	if startsEast(camera) {
		// cameras will only see every other row and there is the zero-indexing issue, hence the initially east facing
		// cameras will progress 1 1 3 3 5 5 7 7 9 9 i.e. all the odd rows with alternating orientation
		if row%2 == 0 {
			return row + 1
		} else {
			return row
		}
	} else {
		// initially west facing cameras will progress 0 0 2 2 4 4 etc
		if row%2 == 0 {
			return row
		} else {
			return row + 1
		}
	}
}

// startsEast returns true if the camera (0,1,2,3) initially has an eastward orientation
func startsEast(camera int) bool {
	return camera == 0 || camera == 1
}

// calcDirection determines the direction the image was oriented based on the camera and row
func calcDirection(camera int, row int) string {

	isEven := row%2 == 0

	// the rover always started south with camera in the following position:
	// 1  ^  3
	// 2     4
	// for the second row, the rover faced the north, hence the orientation flips every other row
	if (isEven && startsEast(camera)) || (!isEven && !startsEast(camera)) {
		return EAST
	} else {
		return WEST
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

	// write out the header
	header := []string{"path", "date", "time", "camera", "row", "bay", "direction", "has_post"}
	writer.Write(header)

	// write all the bay predictions
	for c := 0; c < CAMERAS; c++ {

		// write out each row
		for i := 0; i < len(bays[c]); i++ {

			currentRow := bays[c][i]

			//write out each bay
			for j := 0; j < len(currentRow.bays); j++ {

				currentBay := currentRow.bays[j]

				//write out all the images
				for k := 0; k < len(currentBay.images); k++ {
					img := currentBay.images[k]

					// zero is the ID for East
					dir := "0"
					if img.direction == WEST {
						dir = "1"
					}

					// include the post information
					post := "0"
					if img.hasPost {
						post = "1"
					}

					//i = row, j = bay
					row := []string{img.path, img.date, img.time, fmt.Sprint(img.cameraNum), fmt.Sprint(img.row), fmt.Sprint(currentBay.bayNum), dir, post}
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

	// make an initial model
	start := makeInitialGroups(images)

	// make an initial assignments
	model := initialDPModel(images)
	//model := initialPoissonModel(images)

	fmt.Println("Starting Groups")
	showRows(start)
	model.Show()
	fmt.Println()

	// use EM to correct the assignments
	result := em(&model, start, *rounds)

	fmt.Println("Results")
	model.Show()

	// show the row assignments
	showRows(result)

	// if an output file is given, write to it
	if *outFile != "" {
		writeBays(*outFile, result)
	}
}
