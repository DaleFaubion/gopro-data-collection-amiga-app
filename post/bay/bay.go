package main

// Bay an ent of images to a particular bay in a single row
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
