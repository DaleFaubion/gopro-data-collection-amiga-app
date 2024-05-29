package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"strings"
)

//rows 0 and 22 (zero-based indexing) are out of the block

const NUM_ROWS = 23
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

// parseTime finds the time embedded in the path
func parseTime(path string) string {
	const TIME = 1
	parts := strings.Split(path, "/")
	last := parts[len(parts)-1]

	nameParts := strings.Split(last, "_")
	return nameParts[TIME]
}

// loadImages reads a CSV with image metadata
func loadImages(path string, date string) []Image {
	const PATH = 0
	const DATE = 1
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
		path := record[PATH]
		imgDate := record[DATE]
		imgTime := parseTime(path)
		camera := cameraNum(path)
		post := record[POST]

		//only include images for the given day
		if imgDate == date {
			img := Image{path, imgDate, imgTime, post == "1", -1, camera, ""}
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
			return row - 1
		}
	}
}

// showAssignments displays all the assignments
func showAssignments(assignments []Assignment) {

	// for each camera print off the row assignments
	for c, assignment := range assignments {
		fmt.Printf("For camera %d\n", c)

		for i := 0; i < NUM_ROWS; i++ {
			fmt.Printf("|     %2d    ", i)
		}

		fmt.Println()

		for _, row := range assignment.rows {
			left, right := row.numPosts()
			reg := row.numRegular()

			fmt.Printf("| %2d_%2d_%2d ", left, reg, right)
		}

		fmt.Println("|")
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

	defer file.Close()

	// create a writer
	writer := csv.NewWriter(file)

	//write out all the predicted rows
	for c := 0; c < len(assignments); c++ {
		for _, row := range assignments[c].rows {
			for _, img := range row.images {
				row := []string{img.path, img.date, img.time, fmt.Sprint(img.row), fmt.Sprint(img.cameraNum + 1), img.direction}
				writer.Write(row)
			}
		}
	}
}

//main runs a program to predict row assignment based on post predictions and
func main() {

	// get the commandline arguments
	// Set up the optional flags
	rounds := flag.Int("rounds", 1000, "The number of rounds to apply EM")
	outFile := flag.String("out_file", "", "The path to the CSV file to write with the bay predictions")

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

	regularImages := 0

	for _, image := range postData {
		if !image.hasPost {
			regularImages++
		}
	}

	// make the initial model
	model := NewModel(float64(regularImages) / float64(NUM_ROWS))

	// run EM
	best := model.em(*rounds, start)

	// update images based on the assignments
	updateImages(best)

	// display the results
	showAssignments(best)

	// write out the results
	if *outFile != "" {
		writeAssignments(*outFile, best)
	}
}
