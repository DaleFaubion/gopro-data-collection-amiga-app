package main

/*
This file defines the row struct to represent a sequence of images along with associated methods
*/

type Row struct {
	images []Image
}

// NewRow make a new, empty row
func newRow() Row {
	row := Row{[]Image{}}
	return row
}

// appendImage appends a new image to the row, returns a new row
func (row *Row) appendImage(image Image) Row {
	newImages := append(row.images, image)
	return Row{newImages}
}

// prependImage prepends a new image to the row, returns a new row
func (row *Row) prependImage(image Image) Row {
	singleton := []Image{image}
	newImages := append(singleton, row.images...)
	return Row{newImages}
}

// popFirst removes and returns the first image, returns a new row
func (row *Row) popFirst() (Image, Row) {
	first := row.images[0]
	rest := row.images[1:]
	result := Row{rest}
	return first, result
}

// popLast removes and returns the last image, returns a new row
func (row *Row) popLast() (Image, Row) {
	last := row.images[len(row.images)-1]
	rest := row.images[:len(row.images)-1]
	result := Row{rest}
	return last, result
}

// giveToStartOf removes an image from the end of this row and gives it to the start of the other row, returns
// two new rows
func (row *Row) giveToStartOf(other *Row) (Row, Row) {
	toGive, newLeft := row.popLast()
	newRight := other.prependImage(toGive)
	return newLeft, newRight
}

// takeFromStartOf takes the first image from the other row and appends it to this one, returns two new rows
func (row *Row) takeFromStartOf(other *Row) (Row, Row) {
	toGive, newRight := other.popFirst()
	newLeft := row.appendImage(toGive)
	return newLeft, newRight
}

// split cuts a row in half creating a new row
func (row *Row) split() (Row, Row) {
	mid := row.numImages() / 2
	left := Row{row.images[:mid]}
	right := Row{row.images[mid:]}
	return left, right
}

// merge combines two rows into a single new row
func (row *Row) merge(other *Row) Row {
	newImages := row.images
	newImages = append(newImages, other.images...)
	return Row{newImages}
}

// hasImages returns true if there are images in the row
func (row *Row) hasImages() bool {
	return len(row.images) > 0
}

// numPosts returns the number of images that contain a post in the row
func (row *Row) numPosts() (int, int) {
	start := 0
	end := 0
	index := 0

	// count all the starting images with posts
	for index < len(row.images) && row.images[index].hasPost {
		start += 1
		index += 1
	}

	//count all the end images with posts
	index = len(row.images) - 1

	for index >= 0 && row.images[index].hasPost {
		end += 1
		index -= 1
	}

	// check if the row is all posts, if so, divide up the counts between the start and the end
	if start == len(row.images) {
		start = len(row.images) / 2
		end = len(row.images) - start
	}

	return start, end
}

// numBadPosts returns the number of images that contain a post that are neither at the beginning nor at the end of the row
func (row *Row) numBadPosts() int {
	posts := row.numImages() - row.numRegular()
	left, right := row.numPosts()
	return posts - left - right
}

// numEmpty returns the number of images that do not contain a post in the row
func (row *Row) numRegular() int {
	count := 0

	for _, img := range row.images {
		if !img.hasPost {
			count++
		}
	}

	return count
}

// NumImages returns the number of images in the row
func (row *Row) numImages() int {
	return len(row.images)
}
