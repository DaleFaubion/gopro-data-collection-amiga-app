package main

import (
	"fmt"
	"math"
	"testing"
)

// MakeImage produces a test image
func MakeImage(camera int, hasPost bool) Image {

	var row int
	var direction string

	if camera == 1 || camera == 2 {
		//if the camera is 1 or 2, the camera should be facing East towards row 3
		row = 3
		direction = "East"
	} else {
		//else the camera should be West, pointing towards row 2
		row = 2
		direction = "West"
	}

	img := Image{
		"",
		"",
		"",
		hasPost,
		row,
		camera,
		direction,
	}

	return img
}

func MakeRow(camera int, hasPost ...int) []Image {
	results := make([]Image, 0)

	for _, postInt := range hasPost {

		post := postInt == 1

		results = append(results, MakeImage(camera, post))
	}

	return results
}

var cleanData = [][]Image{
	MakeRow(1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1),
	MakeRow(2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1),
	MakeRow(3, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1),
	MakeRow(4, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1),
}

var shortCleanData = [][]Image{
	MakeRow(1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0),
	MakeRow(2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0),
	MakeRow(3, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0),
	MakeRow(4, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0),
}

func Test_Viterbi_short(t *testing.T) {
	const EXP_STATES = 4
	const EXP_SIZE = 4
	model := PostModel{.95, EXP_SIZE, 1, 4, EXP_STATES}

	testRow := Row{3, shortCleanData}

	states := model.viterbi(testRow)

	for _, state := range states {
		fmt.Println("state", state)
	}

	if len(states) != EXP_STATES {
		t.Errorf("Found %d states, expected %d", len(states), EXP_STATES)
	}

	for _, state := range states {
		size := (state.end - state.start) + 1
		if size != EXP_SIZE {
			t.Errorf("State %d, Found %d images, expected %d", state.state, size, EXP_SIZE)
		}
	}

}

func Test_Viterbi(t *testing.T) {
	const EXP_STATES = 7
	const EXP_SIZE = 4
	model := PostModel{.95, 4, 1, 4, EXP_STATES}

	testRow := Row{3, cleanData}

	states := model.viterbi(testRow)

	for _, state := range states {
		fmt.Println("state", state)
	}

	if len(states) != EXP_STATES {
		t.Errorf("Found %d states, expected %d", len(states), EXP_STATES)
	}

	for _, state := range states {
		size := (state.end - state.start) + 1
		if size != EXP_SIZE {
			t.Errorf("State %d, Found %d images, expected %d", state.state, size, EXP_SIZE)
		}
	}
}

func Test_TransitionProb(t *testing.T) {
	model := PostModel{.95, 4, 1, 4, 7}
	target := math.Log(NormalCDF(4, model.groupMean, model.groupStDev))
	prob := model.transitionProb(4)

	if target != prob {
		t.Errorf("Expected a probabilty of %.4f when %.4f was received", target, prob)
	}
}

func Test_ObservationProb_Clean_FirstPostGroup(t *testing.T) {
	model := PostModel{.95, 4, 1, 4, 7}
	prob := model.observationProb(cleanData, 0, 3, true)

	//the parameterization of this is towards missing posts
	targetProb := BinomialLogProb(4, 0, 1.0-.95)

	if prob != targetProb {
		t.Errorf("Expected a probabiltiy of %.4f but got %.4f", targetProb, prob)
	}
}

func Test_ObservationProb_Clean_FirstNoPostGroup(t *testing.T) {

	model := PostModel{.95, 4, 1, 4, 7}
	prob := model.observationProb(cleanData, 4, 7, false)

	targetProb := BinomialLogProb(4, 4, .95)

	if prob != targetProb {
		t.Errorf("Expected a probabiltiy of %.4f but got %.4f", targetProb, prob)
	}
}

func Test_ObservationProb_Clean_SecondPostGroup(t *testing.T) {
	model := PostModel{.95, 4, 1, 4, 7}
	prob := model.observationProb(cleanData, 8, 11, true)

	//the parameterization of this is towards missing posts
	targetProb := BinomialLogProb(4, 0, 1.0-.95)

	if prob != targetProb {
		t.Errorf("Expected a probabiltiy of %.4f but got %.4f", targetProb, prob)
	}
}

func Test_ObservationProb_Clean_SecondNoPostGroup(t *testing.T) {

	model := PostModel{.95, 4, 1, 4, 7}
	prob := model.observationProb(cleanData, 12, 15, false)

	targetProb := BinomialLogProb(4, 4, .95)

	if prob != targetProb {
		t.Errorf("Expected a probabiltiy of %.4f but got %.4f", targetProb, prob)
	}
}
