package main

import (
	"testing"
)

func TestLoadImages(t *testing.T) {
	images := loadImages("../test-data/post-pred.csv", "2022-06-16")

	if len(images) != 15 {
		t.Errorf("Expected 15 images, got %d", len(images))
	}

	withPosts := 0

	for _, image := range images {
		if image.hasPost {
			withPosts++
		}
	}

	if withPosts != 10 {
		t.Errorf("Expected 10 posts, got %d", withPosts)
	}
}

func TestCalcDirCam0Row0(t *testing.T) {
	if calcDirection(0, 0) != "East" {
		t.Errorf("Expected East, got %s", calcDirection(0, 0))
	}
}

func TestCalcDirCam0Row1(t *testing.T) {
	if calcDirection(0, 1) != "West" {
		t.Errorf("Expected West, got %s", calcDirection(0, 1))
	}
}

func TestCalcDirCam2Row1(t *testing.T) {
	if calcDirection(2, 1) != "East" {
		t.Errorf("Expected East, got %s", calcDirection(2, 1))
	}
}

func TestCalcDirCam2Row0(t *testing.T) {
	if calcDirection(2, 0) != "West" {
		t.Errorf("Expected West, got %s", calcDirection(2, 0))
	}
}

func TestCalcDirCam2Row10(t *testing.T) {
	if calcDirection(2, 10) != "West" {
		t.Errorf("Expected West, got %s", calcDirection(2, 10))
	}
}

func TestCalcRowCam0Row0(t *testing.T) {
	if calcRow(0, 0) != 1 {
		t.Errorf("Expected 1, got %d", calcRow(0, 0))
	}
}

func TestCalcRowCam0Row1(t *testing.T) {
	if calcRow(0, 1) != 1 {
		t.Errorf("Expected 1, got %d", calcRow(0, 1))
	}
}

func TestCalcRowCam0Row2(t *testing.T) {
	if calcRow(0, 2) != 3 {
		t.Errorf("Expected 3, got %d", calcRow(0, 2))
	}
}

func TestCalcRowCam0Row5(t *testing.T) {
	if calcRow(0, 5) != 5 {
		t.Errorf("Expected 5, got %d", calcRow(0, 5))
	}
}

func TestCalcRowCam0Row12(t *testing.T) {
	if calcRow(0, 12) != 13 {
		t.Errorf("Expected 13, got %d", calcRow(0, 12))
	}
}

func TestCalcRowCam2Row0(t *testing.T) {
	if calcRow(2, 0) != 0 {
		t.Errorf("Expected 0, got %d", calcRow(2, 0))
	}
}

func TestCalcRowCam2Row1(t *testing.T) {
	if calcRow(2, 1) != 0 {
		t.Errorf("Expected 0, got %d", calcRow(2, 1))
	}
}

func TestCalcRowCam2Row2(t *testing.T) {
	if calcRow(2, 2) != 2 {
		t.Errorf("Expected 2, got %d", calcRow(2, 2))
	}
}

func TestCalcRowCam2Row5(t *testing.T) {
	if calcRow(2, 5) != 4 {
		t.Errorf("Expected 4, got %d", calcRow(2, 5))
	}
}

func TestCalcRowCam2Row12(t *testing.T) {
	if calcRow(2, 12) != 12 {
		t.Errorf("Expected 12, got %d", calcRow(12, 12))
	}
}

func TestUpdateImages(t *testing.T) {

	imgStart := Image{
		"path/to/img.jpg",
		"2024-05-28",
		"18-01-01",
		false,
		-1,
		0,
		"",
	}

	single := newAssignment()
	single.appendImage(0, imgStart)
	start := []Assignment{single}

	updateImages(start)

	img := start[0].rows[0].images[0]

	if img.row != 1 {
		t.Errorf("Expected row 1, got %d", img.row)
	}

	if img.direction != "East" {
		t.Errorf("Expected East, got %s", img.direction)
	}
}
