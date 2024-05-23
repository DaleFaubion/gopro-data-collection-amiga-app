package main

import "math"

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

type Row struct {
	rowNum int
	images []Image
}

// AppendImage appends a new image to the row, returns a new row
func (row *Row) AppendImage(image Image) Row {
	newImages := append(row.images, image)
	return Row{row.rowNum, newImages}
}

// PrependImage prepends a new image to the row, returns a new row
func (row *Row) PrependImage(image Image) Row {
	singleton := []Image{image}
	newImages := append(singleton, row.images...)
	return Row{row.rowNum, newImages}
}

// PopFirst removes and returns the first image, returns a new row
func (row *Row) PopFirst() (Image, Row) {
	first := row.images[0]
	rest := row.images[1:]
	result := Row{row.rowNum, rest}
	return first, result
}

// PopLast removes and returns the last image, returns a new row
func (row *Row) PopLast() (Image, Row) {
	last := row.images[len(row.images)-1]
	rest := row.images[:len(row.images)-1]
	result := Row{row.rowNum, rest}
	return last, result
}

// GiveToStartOf removes an image from the end of this row and gives it to the start of the other row, returns
// two new rows
func (row *Row) GiveToStartOf(other *Row) (Row, Row) {
	toGive, newLeft := row.PopLast()
	newRight := other.PrependImage(toGive)
	return newLeft, newRight
}

// TakeFromStartOf takes the first image from the other row and appends it to this one, returns two new rows
func (row *Row) TakeFromStartOf(other *Row) (Row, Row) {
	toGive, newRight := other.PopFirst()
	newLeft := row.AppendImage(toGive)
	return newLeft, newRight
}

// HasImages returns true if there are images in the row
func (row *Row) HasImages() bool {
	return len(row.images) > 0
}

// NumPosts returns the number of images that contain a post in the row
func (row *Row) NumPosts() int {
	count := 0

	for _, image := range row.images {
		if image.hasPost {
			count++
		}
	}

	return count
}

// NumEmpty returns the number of images that do not contain a post in the row
func (row *Row) NumEmpty() int {
	return row.NumImages() - row.NumPosts()
}

// NumImages returns the number of images in the row
func (row *Row) NumImages() int {
	return len(row.images)
}

// TODO make a method to generate new row assignments

// TODO make a model struct

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

// TODO make a function to load predicted posts

// TODO make a function to show the row assignments

// TODO make a function to do EM

//main runs a program to predict row assignment based on post predictions and
func main() {
	//TODO finish
}
