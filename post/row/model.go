package main

import (
	"fmt"
	"math"
)

type Model struct {
	LeftPost   float64
	RegularImg float64
	RightPost  float64
}

// NewModel creates a new model
func NewModel(perRow float64) Model {
	model := Model{
		1.0,
		perRow,
		1.0,
	}

	return model
}

// em performs the expectation-maximization algorithm over all the row assignments, returning the best assignment
func (model *Model) em(rounds int, init []Assignment) []Assignment {

	best := make([]Assignment, len(init))
	copy(best, init)

	//TODO add check for convergence
	//for a fixed number of rounds, run the EM algorithms
	for i := 0; i < rounds; i++ {

		// predict the best (max) assignment for each camera
		for c, assignment := range best {
			best[c] = model.maxAssignment(assignment)
		}

		// estimate the parameters
		model.estimate(best)

		if i%100 == 0 {
			fmt.Printf("Round %5d: %.4f\n", i, model.logLikelihood(best))
		}
	}

	return best
}

//maxAssignment finds the best assignment under the current model
func (model *Model) maxAssignment(start Assignment) Assignment {
	best := start
	bestLike := model.assignmentLogLikelihood(&start)

	for _, candidate := range start.generateAssignments() {

		like := model.assignmentLogLikelihood(&candidate)

		if like > bestLike {
			best = candidate
			bestLike = like
		}
	}

	return best
}

// rowLogLikelihood computes the log likelihood of the row assignment
func (model *Model) rowLogLikelihood(row *Row) float64 {
	left, right := row.numPosts()
	regular := row.numRegular()

	return PoissonLogProb(model.LeftPost, left) + PoissonLogProb(model.RightPost, right) + PoissonLogProb(model.RegularImg, regular)
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
	regular := 0
	groups := 0

	// count up the number of groups of posts
	for _, assignment := range overall {
		for _, row := range assignment.rows {
			leftPosts, rightPosts := row.numPosts()
			regCount := row.numRegular()

			left += leftPosts
			right += rightPosts
			regular += regCount
			groups += 1
		}
	}

	total := float64(groups)

	//update the model parameters
	model.LeftPost = float64(left) / total
	model.RightPost = float64(right) / total
	model.RegularImg = float64(regular) / total
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
