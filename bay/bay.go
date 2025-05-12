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

	//move until the next post image
	for !toGive.hasPost && newLeft.NumImages() > 1 {
		toGive, newLeft = newLeft.PopLast()
		newRight = newRight.PrependImage(toGive)
	}

	return newLeft, newRight
}

// TakeFromStartOf takes the first image from the other bay and appends it to this one, returns two new bays
func (bay *Bay) TakeFromStartOf(other *Bay) (Bay, Bay) {
	toGive, newRight := other.PopFirst()
	newLeft := bay.AppendImage(toGive)

	//move until to the next post image
	for !toGive.hasPost && newRight.NumImages() > 1 {
		toGive, newRight = newRight.PopFirst()
		newLeft = newLeft.AppendImage(toGive)
	}

	return newLeft, newRight
}

// HasImages returns true if there are images in the bay
func (bay *Bay) HasImages() bool {
	return len(bay.images) > 0
}

// NumEmpty returns the number of images that do not contain a post in the bay
func (bay *Bay) NumEmpty() int {
	start, end := bay.NumPosts()
	return bay.NumImages() - start - end
}

// NumImages returns the number of images in the bay
func (bay *Bay) NumImages() int {
	return len(bay.images)
}

// MiddlePosts returns the number of posts in the middle of a bay i.e. likely mistakes in post-prediction
func (bay *Bay) MiddlePosts() int {

	total := 0

	for _, img := range bay.images {
		if img.hasPost {
			total++
		}
	}

	left, right := bay.NumPosts()
	return total - left - right
}

// NumPosts returns the number of images that contain a post in the both the start and end of a bay
func (bay *Bay) NumPosts() (int, int) {
	start := 0
	end := 0
	index := 0

	// count all the starting images with posts
	for index < len(bay.images) && bay.images[index].hasPost {
		start += 1
		index += 1
	}

	//count all the end images with posts
	index = len(bay.images) - 1

	for index >= 0 && bay.images[index].hasPost {
		end += 1
		index -= 1
	}

	// check if the bay is all posts, if so, divide up the counts between the start and the end
	if start == len(bay.images) {
		start = len(bay.images) / 2
		end = len(bay.images) - start
	}

	return start, end
}
