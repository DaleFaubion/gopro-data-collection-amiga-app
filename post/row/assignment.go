package main

import (
	"sort"
)

/*
This file defines an assignment, a pictures determined to be part of individual rows, along with associated
methods
*/

// Assignment a data structure to represent row assignments for all the images
type Assignment struct {
	rows []Row
}

// makeInitialAssignment creates an initial assignment per camera
func makeInitialAssignment(images []Image) []Assignment {
	cameraGroups := make([][]Image, NUM_CAMERAS)
	results := make([]Assignment, NUM_CAMERAS)

	// put the images into the correct camera groups
	for _, image := range images {
		cameraGroups[image.cameraNum-1] = append(cameraGroups[image.cameraNum-1], image)
	}

	// ensure that the data is stored by the timestamp
	for c := 0; c < NUM_CAMERAS; c++ {
		sort.Slice(cameraGroups[c], func(i, j int) bool {
			return cameraGroups[c][i].time < cameraGroups[c][j].time
		})
	}

	// initialize each assignment for each camera
	for i := 0; i < NUM_CAMERAS; i++ {
		results[i] = newAssignment()
	}

	// evenly distribute the images in each row
	for i := 0; i < NUM_CAMERAS; i++ {
		count := len(cameraGroups[i])
		perRow := count / NUM_ROWS

		// "round up" if there is a fraction
		if count%NUM_ROWS != 0 {
			perRow++
		}

		for j, image := range cameraGroups[i] {
			rowIdx := j / perRow
			results[i].appendImage(rowIdx, image)
		}
	}

	return results
}

// NewAssignment creates a new empty assignment
func newAssignment() Assignment {
	assignment := Assignment{}
	assignment.rows = make([]Row, NUM_ROWS)
	return assignment
}

// generateAssignments creates new assignments by shifting images from row to row
func (assignment *Assignment) generateAssignments() []Assignment {
	var results []Assignment

	for i := 0; i < NUM_ROWS-1; i++ {

		// move an image to the "left" i.e. this row
		if assignment.rows[i+1].numImages() > 0 {
			results = append(results, assignment.shiftLeft(i))
		}

		// move an image to the "right" i.e. the next row
		if assignment.rows[i].numImages() > 0 {
			results = append(results, assignment.shiftRight(i))
		}
	}

	return results
}

// appendImage adds an image to the end of a row
func (assignment *Assignment) appendImage(rowIdx int, image Image) {
	assignment.rows[rowIdx] = assignment.rows[rowIdx].appendImage(image)
}

// update replaces a row in the assignment with a new row
func (assignment *Assignment) update(index int, row Row) Assignment {
	newImgs := []Row{}
	left := assignment.rows[:index]
	right := assignment.rows[index+1:]
	results := append(newImgs, left...)
	results = append(results, row)
	results = append(results, right...)
	return Assignment{results}
}

// shiftLeft moves an image from the start of the row at index + 1 and moving to the end of the row at the index
func (assignment *Assignment) shiftLeft(index int) Assignment {
	row := assignment.rows[index]
	next := assignment.rows[index+1]
	toLeft, toRight := row.takeFromStartOf(&next)
	result := assignment.update(index, toLeft)
	result = result.update(index+1, toRight)
	return result
}

// shiftRight moves an image from the end of the row at the index to the start of the row at index + 1
func (assignment *Assignment) shiftRight(index int) Assignment {
	row := assignment.rows[index]
	next := assignment.rows[index+1]
	toLeft, toRight := row.giveToStartOf(&next)
	result := assignment.update(index, toLeft)
	result = result.update(index+1, toRight)
	return result
}

// splitAndMerge will split the row at the current index
/*func (assignment *Assignment) splitAndMerge(index int) []Assignment {

}


// TODO consider deleting this
// mergeSmallest combines the two smallest rows
func (assignment *Assignment) mergeSmallestToTheRightOf(index int) Assignment {

	// to account for the pair and the inclusiveness of the slice
	const offset = 2

	small := assignment.smallestPair(index)

	// slice up the current rows into before and after the pair
	before := assignment.rows[:small]
	after := assignment.rows[small+offset:]

	// make a new row from merging the two rows
	merged := assignment.rows[small].merge(&assignment.rows[small+1])

	rows := append(before, merged)
	rows = append(rows, after...)

	// splice in the new row to make a new assignment
	return Assignment{rows}
}

//TODO consider deleting this
// splitAt replaces the row at i and inserts a new row at i + 1 with the two rows created by splitting the row at i
func (assignment *Assignment) splitAt(index int) Assignment {

	// get the slices before and after the row at the index
	target := assignment.rows[index]
	before := assignment.rows[:index]
	after := assignment.rows[index+1:]

	// split the row into two
	mid := len(target.images) / 2
	left := Row{target.images[:mid]}
	right := Row{target.images[mid:]}

	// create a new slice of rows by putting the two new rows in the middle of the existing rows
	results := append(before, left, right)
	results = append(results, after...)

	return Assignment{results}
}

//TODO consider deleting this
// smallestPair returns the index (the second is index + 1), of the pair of smallest rows
func (assignment *Assignment) smallestPair(start int) int {
	smallest := start
	smallestValue := assignment.rows[smallest].numImages() + assignment.rows[smallest+1].numImages()

	for i := start; i < len(assignment.rows)-1; i++ {
		value := assignment.rows[i].numImages() + assignment.rows[i+1].numImages()

		if value < smallestValue {
			smallest = i
			smallestValue = value
		}
	}

	return smallest
}
*/
