package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

const NUM_ROWS = 37
const NUM_BAYS = 14 // May be 14/15
// TODO check if we need to make it less (since the first bay has one vine)

const CAMERAS = 4

// const CAMERAS = 1
const WEST = "West"
const EAST = "East"

const EAST_IDX = "0"
const WEST_IDX = "1"

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

// loadPostData loads the post predictions from a given CSV file
func loadPostData(path string) map[string]bool {
	const pathIdx = 0
	const postIdx = 3
	const oldPostIdx = 1
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

		idx := postIdx

		//use the old post index for older post files
		if len(record) < idx {
			idx = oldPostIdx
		}

		imgPath := record[pathIdx]
		results[imgPath] = record[idx] == hasPost
	}

	return results
}

// loadRowData reads the CSV file and constructs an array of images
func loadRowData(posts map[string]bool, path string) []Image {
	const pathIdx = 0
	const dateIdx = 1
	const timeIdx = 2
	const rowIdx = 3
	const cameraIdx = 4
	const dirIdx = 5

	const defaultDir = "1"
	const defaultCam = 1

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

		imgPath := record[pathIdx]

		//skip first row if it is a header
		if imgPath == "path" {
			continue
		}

		row, _ := strconv.Atoi(record[rowIdx])

		var camera int
		var direction string

		//check if the row file is "new" and has all the fields
		if cameraIdx >= len(record) {
			camera = getCamera(imgPath)
			//calcDirection is expecting the camera index i.e. 0,1,2,3
			direction = calcDirection(camera-1, row)

		} else {
			camera, _ = strconv.Atoi(record[cameraIdx])
			direction = record[dirIdx]

			if direction == EAST_IDX {
				direction = EAST
			} else if direction == WEST_IDX {
				direction = WEST
			}
		}

		hasPost, _ := posts[imgPath]

		newImage := Image{imgPath, record[dateIdx], record[timeIdx], hasPost, row, camera, direction}
		results = append(results, newImage)
	}

	return results
}

// getCamera parses the path and retrieves the camera id
func getCamera(path string) int {
	parts := strings.Split(path, "/")

	//get the second from the last part of the path i.e. the last directory which is the camera
	idx := len(parts) - 2

	camera, _ := strconv.Atoi(parts[idx])

	return camera
}

// buildRows organizes images into rows/camera groups
func buildRows(images []Image, singleCam bool) []Row {

	//find the max row in the data
	maxRow := 0
	for _, image := range images {
		if image.row > maxRow {
			maxRow = image.row
		}
	}

	results := make([]Row, maxRow)

	//initialize the rows
	for i := 0; i < len(results); i++ {
		images := make([][]Image, NUM_CAMERAS)
		results[i] = Row{i + 1, images}
	}

	//put all the images into the correct rows
	for _, image := range images {
		camIdx := image.cameraNum - 1

		//for the single camera setup, make sure the index does not become -1
		if camIdx == -1 || singleCam {
			camIdx = 0

			//make sure the camera number is 1
			image.cameraNum = 1
		}

		rowIdx := calcRowIndex(camIdx, image.row, image.direction)

		if singleCam {
			rowIdx = image.row - 1
		}

		//drop images that face away from the block i.e. row 1 camera 3, facing West
		if rowIdx < maxRow && rowIdx >= 0 {
			row := results[rowIdx]
			row.images[camIdx] = append(row.images[camIdx], image)
		}
	}

	//ensure that the images for each row and camera are in sorted order according to time
	for _, row := range results {
		for _, camRow := range row.images {
			sort.Slice(camRow, func(i, j int) bool {
				return camRow[i].time < camRow[j].time
			})
		}
	}

	return results
}

// ShowRows prints off the row
func showRows(rows []CameraAssignment) {

	for c := 0; c < CAMERAS; c++ {

		fmt.Printf("For camera %d\n\n", c+1)

		//print off the header
		fmt.Printf("    |")

		for i := 1; i <= NUM_BAYS; i++ {
			fmt.Printf("%3d  |", i)
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
				//start, end := bay.NumPosts()
				//fmt.Printf("%2d+%2d+%2d |", start, bay.NumEmpty(), end)
				fmt.Printf("%3d  |", bay.NumImages())
			}
			fmt.Println()
		}

		fmt.Println()
	}
}

func showSingleCamResults(rows []CameraAssignment) {
	var results []RowAssignment = rows[0]

	//print off the header
	fmt.Printf("    |")

	for i := 1; i <= NUM_BAYS; i++ {
		fmt.Printf("%5d    |", i)
	}
	fmt.Println()

	//display each row
	for i, row := range results {

		fmt.Printf("%2d  |", i+1)

		for _, bay := range row.bays {
			fmt.Printf("%5d    |", bay.NumImages())
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

// calcRowIndex determines the index of the row based on the actual row number and the camera
// this is the inverse of the function calcRow
func calcRowIndex(cameraIdx int, row int, direction string) int {

	rowIdx := row - 1

	if travelingSouth(cameraIdx, direction) && startsEast(cameraIdx) {
		//cameras 1 & 2, oriented south, keep the current row
		return rowIdx
	} else if travelingSouth(cameraIdx, direction) && !startsEast(cameraIdx) {
		//cameras 3 & 4, oriented south, move to the next row
		return rowIdx + 1
	} else if !travelingSouth(cameraIdx, direction) && startsEast(cameraIdx) {
		//cameras 1 & 2, oriented north, move the next row
		return rowIdx + 1
	} else {
		//cameras 3 & 4, oriented north, keep the current row
		return rowIdx
	}
}

// travelingSouth determines if the rover was moving south when the picture was taken
func travelingSouth(cameraIdx int, direction string) bool {

	/*        ^                 ^
	          S                 N
		<-- E  W -->      <--W     E-->
		|	      |       |          |
		|  1   3  |       |  1    3  |
		|         |       |          |
		|  2   4  |       |  2    4  |
		|         |       |          |
	*/

	return (direction == EAST && startsEast(cameraIdx)) || (direction == WEST && !startsEast(cameraIdx))
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
func writeBays(path string, bays []CameraAssignment, singleCam bool) {
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

					if singleCam {
						dir = "0"
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
	postProb := flag.Float64("post", 0.95, "The conditional probability of an image containing a post in a post group")
	groupMean := flag.Float64("mean", 4.0, "The average number of pictures per post/no post grouping")
	// TODO make numGroups calculated based on # bays constant
	numGroups := flag.Int("numGroups", 31, "The number of post/no post groups per row i.e. # bays x 2 + 1")
	thres := flag.Int("thres", 3, "The threshold of simultaneous post images counting as a true post")
	singleCam := flag.Bool("single", false, "Whether the data has only a single camera or not i.e. for the years 2019-2021")
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

	fmt.Printf("Number of images: %d\n", len(images))

	model := PostModel{*postProb, *groupMean, *thres, *numGroups}

	fmt.Printf("Post model %v\n", model)

	rows := buildRows(images, *singleCam)

	fmt.Printf("Number of rows: %d\n", len(rows))

	result := model.dpAssignment(rows)

	fmt.Println("Results")

	// show the row assignments
	if *singleCam {
		showSingleCamResults(result)
	} else {
		showRows(result)
	}

	// if an output file is given, write to it
	if *outFile != "" {
		writeBays(*outFile, result, *singleCam)
	}
}
