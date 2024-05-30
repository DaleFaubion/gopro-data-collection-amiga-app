package main

// RowAssignment the ent of images to bays in a single row
type RowAssignment struct {
	rowNum int
	bays   []Bay
}

// NewRowAssignment creates a new row ent
func NewRowAssignment(rowNum int) RowAssignment {
	ent := RowAssignment{}
	ent.rowNum = rowNum
	ent.bays = make([]Bay, NUM_BAYS)
	return ent
}

// ReplaceBays update the ent, with a bay, creates a new ent
func (row *RowAssignment) ReplaceBays(firstIdx int, left Bay, secondIdx int, right Bay) RowAssignment {
	newBays := make([]Bay, len(row.bays))
	copy(newBays, row.bays)
	newBays[firstIdx] = left
	newBays[secondIdx] = right
	return RowAssignment{row.rowNum, newBays}
}

// NumImages counts up the number of images in the row
func (row *RowAssignment) NumImages() int {
	total := 0

	for _, bay := range row.bays {
		total += bay.NumImages()
	}

	return total
}

//generateAssignments creates new ents by moving single images to adjacent bays
func (row *RowAssignment) generateAssignments() []RowAssignment {
	var results []RowAssignment

	// generate two new ents per each pair of bays, i.e. move an image from left to right and
	// from right to left
	for i := 0; i < len(row.bays)-1; i++ {
		left := row.bays[i]
		right := row.bays[i+1]

		if right.NumImages() > 1 {
			toLeftLeft, toLeftRight := left.TakeFromStartOf(&right)
			first := row.ReplaceBays(i, toLeftLeft, i+1, toLeftRight)
			results = append(results, first)
		}

		if left.NumImages() > 1 {
			toRightLeft, toRightRight := left.GiveToStartOf(&right)
			second := row.ReplaceBays(i, toRightLeft, i+1, toRightRight)
			results = append(results, second)
		}
	}

	return results
}
