package main

import (
	"fmt"
	"math"
)

type BayModel struct {
	startLambda float64
	imageLambda float64
	endLambda   float64
}

// RowLogLikelihood computes the likelihood of the row ent
func (model *BayModel) rowLogLikelihood(row *RowAssignment) float64 {

	like := 0.0

	for _, bay := range row.bays {

		start, end := bay.NumPosts()

		// compute the probability of the regular images
		reg := PoissonLogProb(model.imageLambda, bay.NumEmpty())

		// compute the probability of the post images
		startLike := PoissonLogProb(model.startLambda, start)

		endLike := PoissonLogProb(model.endLambda, end)

		like += reg + startLike + endLike
	}

	return like
}

// LogLikelihood computes the score for the whole ent
func (model *BayModel) logLikelihood(rows CameraAssignment) float64 {
	like := 0.0

	for _, row := range rows {
		like += model.rowLogLikelihood(&row)
	}

	return like
}

// vineyardLogLikelihood computes the log-likelihood over the whole vineyard assignment
func (model *BayModel) vineyardLogLikelihood(vineyard []CameraAssignment) float64 {
	like := 0.0

	for _, assignment := range vineyard {
		like += model.logLikelihood(assignment)
	}

	return like
}

// em runs the expectation maximization algorithm to find the best row ent
func (model *BayModel) em(init []CameraAssignment, rounds int) []CameraAssignment {

	improved := true
	i := 0
	best := init
	bestLike := model.vineyardLogLikelihood(init)

	// for a fixed number of iterations, run the EM algo
	for i < rounds && improved {

		var next []CameraAssignment

		// for each camera, produce the best assignment
		for j := 0; j < CAMERAS; j++ {
			next = append(next, model.maxAssignment(best[j]))
		}

		// estimate the model parameters
		model.expectedModel(next)
		currentLike := model.vineyardLogLikelihood(next)

		//only keep the changes if it is an improvement
		if currentLike > bestLike {
			best = next
			bestLike = currentLike
		} else {
			improved = false
		}

		if i%5 == 0 {
			fmt.Printf("Round %d: %.4f\n", i, currentLike)
		}

		i++
	}

	fmt.Printf("Round %d: %.4f\n", i-1, bestLike)

	return best
}

// maxAssignment create the maximum likelihood assignment of images under the current model
func (model *BayModel) maxAssignment(assignment CameraAssignment) CameraAssignment {
	var newRows []RowAssignment

	for _, row := range assignment {
		newRows = append(newRows, model.maxRow(row))
	}

	return newRows
}

// maxRow find the row that maximizes the likelihood under the current model
func (model *BayModel) maxRow(row RowAssignment) RowAssignment {

	done := false
	best := row
	bestScore := model.rowLogLikelihood(&best)

	// until there is no improvement, greedily try different candidates
	for !done {

		done = true

		// generate a collection of candidates
		candidates := best.generateAssignments()

		// evaluate all the candidates and pick the best
		for _, candidate := range candidates {

			score := model.rowLogLikelihood(&candidate)

			//if it is an improvement, remember it and continue
			if score > bestScore {
				best = candidate
				bestScore = score
				done = false
			}
		}

	}

	return best
}

// expectedModel updates the models parameters based on the current ent
func (model *BayModel) expectedModel(init []CameraAssignment) {

	avgEmpty := 0.0
	avgStart := 0.0
	avgEnd := 0.0
	total := 0

	// average the number of empty images in all the bays and cameras
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < len(init[c]); i++ {
			for _, bay := range init[c][i].bays {
				start, end := bay.NumPosts()
				avgEmpty += float64(bay.NumEmpty())
				avgStart += float64(start)
				avgEnd += float64(end)
				total += 1
			}
		}
	}

	//average the number of post images in all the bays
	model.imageLambda = avgEmpty / float64(total)
	model.startLambda = avgStart / float64(total)
	model.endLambda = avgEnd / float64(total)
}

// initialModel creates an initial model based on the
func initialModel(images []Image) BayModel {

	// create a set of parameters per row
	emptyCounts := 0.0
	postCounts := 0.0
	total := float64(NUM_ROWS * NUM_BAYS * CAMERAS)

	// for each image, increment the counts
	for _, image := range images {
		if image.hasPost {
			postCounts += 1
		} else {
			emptyCounts += 1
		}
	}

	postLambda := (postCounts / 2) / total
	emptyLambda := emptyCounts / total

	// normalize
	return BayModel{postLambda, emptyLambda, postLambda}
}

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
