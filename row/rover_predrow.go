package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"strings"
)

//rows 0 and 22 (zero-based indexing) are out of the block

const NUM_ROWS = 22
const NUM_CAMERAS = 4

const EAST = "East"
const WEST = "West"

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

// cameraNum parse the camera number out of the path
func cameraNum(path string) int {
	if strings.Contains(path, "/1/") {
		return 1
	} else if strings.Contains(path, "/2/") {
		return 2
	} else if strings.Contains(path, "/3/") {
		return 3
	} else {
		return 4
	}
}

//parseTime extracts the timestamp from the file path
func parseTime(path string) string {
	const timeIdx = 1
	paths := strings.Split(path, "/")
	filename := paths[len(paths)-1]
	parts := strings.Split(filename, "_")
	return parts[timeIdx]
}

// loadImages reads a CSV with image metadata
func loadImages(path string, date string) []Image {
	const PATH = 0
	const DATE = 1
	const TIME = 2
	const POST = 3

	results := []Image{}

	data, fileErr := os.Open(path)

	if fileErr != nil {
		fmt.Println("Error opening file", fileErr)
		os.Exit(1)
	}

	defer data.Close()

	reader := csv.NewReader(data)

	records, readErr := reader.ReadAll()

	if readErr != nil {
		fmt.Println("Error reading file", readErr)
		os.Exit(1)
	}

	for _, record := range records {
		imgPath := record[PATH]
		imgDate := record[DATE]
		imgTime := record[TIME]
		camera := cameraNum(imgPath)
		post := record[POST]

		// parse the time out of the path name if no time was specified
		if imgTime == "" {
			imgTime = parseTime(imgPath)
		}

		//only include images for the given day
		if imgDate == date {
			img := Image{imgPath, imgDate, imgTime, post == "1", -1, camera, ""}
			results = append(results, img)
		}

	}

	return results
}

// updateImages updates the images row and direction based on the assignment
func updateImages(assignments []Assignment) {
	for c, assignment := range assignments {
		for r, row := range assignment.rows {
			for i := 0; i < len(row.images); i++ {
				row.images[i].row = calcRow(c, r)
				row.images[i].direction = calcDirection(c, r)
			}
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

// showModel prints out the model
func showModel(model Model) {
	fmt.Printf("Model (%.2f)  (%.2f) (%.2f)\n", model.LeftPost, model.ImgProb, model.RightPost)
}

// showAssignments displays all the assignments
func showAssignments(assignments []Assignment) {

	// for each camera print off the row assignments
	for c, assignment := range assignments {
		fmt.Printf("For camera %d\n", c)

		for rowIdx, row := range assignment.rows {
			left, right := row.numPosts()
			reg := row.numRegular()
			rowNum := calcRow(c, rowIdx)
			dir := calcDirection(c, rowIdx)

			fmt.Printf("%2d %s | %2d + %3d(%d) + %2d = %d\n", rowNum, dir, left, reg, row.numBadPosts(), right, row.numImages())
		}

		fmt.Println()
	}
}

func writeAssignments(path string, assignments []Assignment) {
	// open the file
	file, fileErr := os.Create(path)

	// exit if there is an error
	if fileErr != nil {
		fmt.Printf("Cannot write to %s\n", path)
		os.Exit(1)
	}

	// create a writer
	writer := csv.NewWriter(file)

	// write out a header row
	header := []string{"path", "date", "time", "row", "camera", "direction", "post"}
	writer.Write(header)

	//write out all the predicted rows
	for c := 0; c < len(assignments); c++ {
		for _, row := range assignments[c].rows {
			for _, img := range row.images {

				post := "1"

				if !img.hasPost {
					post = "0"
				}

				row := []string{img.path, img.date, img.time, fmt.Sprint(img.row), fmt.Sprint(img.cameraNum), img.direction, post}
				writeErr := writer.Write(row)

				if writeErr != nil {
					fmt.Println("Error writing row", row)
				}
			}
		}
	}

	writer.Flush()
	closeErr := file.Close()

	if closeErr != nil {
		fmt.Printf("Error closing file: %s", closeErr)
	}
}

//main runs a program to predict row assignment based on post predictions and
func main() {

	// get the commandline arguments
	// Set up the optional flags
	rounds := flag.Int("rounds", 1000, "The number of rounds to apply EM")
	outFile := flag.String("out", "", "The path to the CSV file to write with the bay predictions")

	flag.Parse()

	if len(flag.Args()) < 2 {
		fmt.Printf("Usage: <date> <post file> [out file]\n")
		os.Exit(1)
	}

	// get the position args
	date := flag.Args()[0]
	postFile := flag.Arg(1)

	// load the post predictions
	postData := loadImages(postFile, date)

	// make the initial assignments
	start := makeInitialAssignment(postData)

	initProb := 0.0
	size := 0
	total := 0

	for _, assignment := range start {
		for _, row := range assignment.rows {
			initProb += float64(row.numRegular()) / float64(row.numImages())
			size += row.numImages()
			total++
		}
	}

	// make the initial model
	model := NewModel(initProb/float64(total), float64(size)/float64(total))

	showModel(model)

	// run EM
	best := model.em(*rounds, start)

	// update images based on the assignments
	updateImages(best)

	// diplay the model
	showModel(model)

	// display the results
	showAssignments(best)

	// write out the results
	if *outFile != "" {
		fmt.Println("Writing to ", *outFile)
		writeAssignments(*outFile, best)
	}
}
