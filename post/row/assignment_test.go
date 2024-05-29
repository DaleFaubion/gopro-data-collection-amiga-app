package main

import (
	"testing"
)

func TestNewAssignment(t *testing.T) {
	assignment := newAssignment()

	if len(assignment.rows) != NUM_ROWS {
		t.Errorf("Expected %d rows, got %d", NUM_ROWS, len(assignment.rows))
	}
}

func TestAssignmentGeneration(t *testing.T) {
	const factor = 2
	assignment := newAssignment()

	//add two images to each row
	for i := 0; i < len(assignment.rows); i++ {
		assignment.appendImage(i, SimpleImage())
		assignment.appendImage(i, SimpleImage())
	}

	//check that the correct number of new assignments is created
	results := assignment.generateAssignments()
	//results := []Assignment{}

	if len(results) != (NUM_ROWS-1)*factor {
		t.Errorf("Expected %d assignments, got %d", (NUM_ROWS-1)*factor, len(results))
	}
}

func TestShiftLeft(t *testing.T) {
	const idx = 10
	const adj = 11

	assignment := newAssignment()

	//add two images to each row
	for i := 0; i < len(assignment.rows); i++ {
		assignment.appendImage(i, SimpleImage())
		assignment.appendImage(i, SimpleImage())
	}

	result := assignment.shiftLeft(idx)

	if result.rows[idx].numImages() != 3 {
		t.Errorf("Expected 3 images, got %d for target row", result.rows[idx].numImages())
	}

	if result.rows[adj].numImages() != 1 {
		t.Errorf("Expected 1 image, got %d for adjacent row", result.rows[adj].numImages())
	}
}

func TestShiftRight(t *testing.T) {
	const idx = 10
	const adj = 11

	assignment := newAssignment()

	//add two images to each row
	for i := 0; i < len(assignment.rows); i++ {
		assignment.appendImage(i, SimpleImage())
		assignment.appendImage(i, SimpleImage())
	}

	result := assignment.shiftRight(idx)

	if result.rows[idx].numImages() != 1 {
		t.Errorf("Expected 1 images, got %d for target row", result.rows[idx].numImages())
	}

	if result.rows[adj].numImages() != 3 {
		t.Errorf("Expected 3 image, got %d for adjacent row", result.rows[adj].numImages())
	}
}
