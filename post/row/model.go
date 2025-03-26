package main

import (
	"fmt"
	"math"
)

type Model struct {
	LeftPost  float64 //lambda (expected mean) of posts starting the row
	ImgProb   float64 //the probability of a picture being a regular picture (no post) given it is in the middle
	RightPost float64 //lambda of posts at the end of the row
	RowSize   float64 //the expected number of images in a row
}

// NewModel creates a new model
func NewModel(prob float64, expectedRow float64) Model {
	model := Model{
		1.0,
		prob,
		1.0,
		expectedRow,
	}

	return model
}

// EPS actually a constant
var EPS = math.Log(0.00000000001)

// em performs the expectation-maximization algorithm over all the row assignments, returning the best assignment
func (model *Model) em(rounds int, init []Assignment) []Assignment {

	i := 0
	improvement := true
	best := make([]Assignment, len(init))
	bestLike := model.logLikelihood(init)
	currentLike := math.Inf(-1)
	copy(best, init)

	//for a fixed number of rounds or until convergence, run the EM algorithms
	for i < rounds && improvement {

		// predict the best (max) assignment for each camera
		for c, assignment := range best {
			best[c] = model.maxAssignment(assignment)
		}

		// estimate the parameters
		model.estimate(best)
		currentLike = model.logLikelihood(best)

		if currentLike > bestLike {
			bestLike = currentLike
		} else {
			improvement = false
		}

		if i%5 == 0 {
			fmt.Printf("Round %5d: %.4f\n", i, currentLike)
		}

		i++
	}

	fmt.Printf("Round %5d: %.4f\n", i-1, currentLike)

	return best
}

//maxAssignment finds the best assignment under the current model
func (model *Model) maxAssignment(start Assignment) Assignment {
	best := start
	bestLike := model.assignmentLogLikelihood(&start)
	done := false

	for !done {

		done = true

		for _, candidate := range best.generateAssignments() {

			like := model.assignmentLogLikelihood(&candidate)

			if like > bestLike {
				best = candidate
				bestLike = like
				done = false
			}
		}

	}

	return best
}

// rowLogLikelihood computes the log likelihood of the row assignment
func (model *Model) rowLogLikelihood(row *Row) float64 {
	left, right := row.numPosts()
	regular := row.numRegular()

	return PoissonLogProb(model.LeftPost, left) + PoissonLogProb(model.RightPost, right) + BinomialLogProb(row.numImages(), regular, model.ImgProb) + PoissonLogProb(model.RowSize, row.numImages())
}

// assignmentLogLikelihood computes the log likelihood of the whole assignment
func (model *Model) assignmentLogLikelihood(assignment *Assignment) float64 {
	like := 0.0

	for _, row := range assignment.rows {
		like += model.rowLogLikelihood(&row)
	}

	return like
}

//computes the log likelihood over all the
func (model *Model) logLikelihood(overall []Assignment) float64 {
	like := 0.0

	for _, assignment := range overall {
		like += model.assignmentLogLikelihood(&assignment)
	}

	return like
}

//estimate updates the model's parameters based on the given assignments
func (model *Model) estimate(overall []Assignment) {
	left := 0
	right := 0
	prob := 0.0
	rowSize := 0.0
	groups := 0

	// count up the number of groups of posts
	for _, assignment := range overall {
		for _, row := range assignment.rows {
			leftPosts, rightPosts := row.numPosts()

			left += leftPosts
			right += rightPosts
			prob += 1.0 - (float64(row.numBadPosts()) / float64(row.numImages()))
			rowSize += float64(row.numImages())
			groups += 1
		}
	}

	total := float64(groups)

	//update the model parameters
	model.LeftPost = math.Max(float64(left)/total, 1.0)
	model.RightPost = math.Max(float64(right)/total, 1.0)
	model.ImgProb = prob / total
	model.RowSize = rowSize / total
}

// PoissonLogProb computes the log probability of a count under a Poisson distribution
func PoissonLogProb(lambda float64, count int) float64 {
	if count <= 0 {
		// use a very small probability instead of zero
		return EPS
	} else {
		// the numerator is lambda^k e^-lambda i.e. in log space: k ln lambda - lambda
		num := (float64(count) * math.Log(lambda)) - lambda

		// the denominator is the sum of 1 to k i.e. the log of the factorial of the count
		denom := logFactorial(count)

		// in log space, the numerator over the denominator is simply subtraction
		return num - denom
	}
}

// BinomialLogProb computes the log probability of a sequence of pictures according to a binomial distribution
// pics is the total i.e. n
// noPosts is the number of "successes"
// prob is "p" according to a standard binomial distribution
func BinomialLogProb(pics int, noPosts int, prob float64) float64 {
	if pics <= 0 {
		return EPS
	} else {
		return logNChooseK(pics, noPosts) + (float64(noPosts) * math.Log(prob)) + (float64(pics-noPosts) * math.Log(1.0-prob))
	}
}

// logNChooseK computes the binomial coefficient in log space
func logNChooseK(n int, k int) float64 {
	return logFactorial(n) - logFactorial(k) - logFactorial(n-k)
}

//logFactorial computes the factorial but in log space
func logFactorial(n int) float64 {
	denom := 0.0
	for i := 1; i <= n; i++ {
		denom += math.Log(float64(i))
	}
	return denom
}
