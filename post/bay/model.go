package main

import (
	"fmt"
	"math"
)

type BayModel struct {
	count       [SECTIONS]float64
	composition [SECTIONS]float64
}

const SECTIONS = 3
const MAX_SECTION = 2
const VINES_PER_BAY = 5.0
const LAST_BAY_VINES = 4.0

var EPS = math.Log(0.00000000001)

func NewBayModel(mean float64, noPostProb float64) BayModel {
	means := [SECTIONS]float64{mean, mean, mean}
	probs := [SECTIONS]float64{1.0 - noPostProb, noPostProb, 1.0 - noPostProb}

	return BayModel{means, probs}
}

func scaleLast(mean float64) float64 {
	return (mean / VINES_PER_BAY) * LAST_BAY_VINES
}

// RowLogLikelihood computes the likelihood of the row ent
func (model *BayModel) rowLogLikelihood(row *RowAssignment) float64 {

	like := 0.0

	for _, bay := range row.bays {

		if bay.NumImages() > 0 {
			partition := model.maxSectionAssignment(&bay)
			like += model.bayLogLikelihood(&bay, partition)
		}
	}

	return like
}

//bayLogLikelihood computes the log likelihood of the bay, give then partition of the images
func (model *BayModel) bayLogLikelihood(bay *Bay, partition []int) float64 {
	like := 0.0

	// add the end of the bay as the final endpoint
	partition = append(partition, bay.NumImages())

	for i := 0; i < len(partition)-1; i++ {
		like += model.sectionLogLike(bay, i, partition[i], partition[i+1])
	}

	return like
}

// maxSectionAssignment computes the assignment of images to sections (0,1,2) (start, middle, end)
// using a dynamic program
// the partition array return
func (model *BayModel) maxSectionAssignment(bay *Bay) []int {
	const MIDDLE = 1
	n := bay.NumImages()

	// early exit for special cases
	if n == 0 {
		return []int{}
	} else if n == 1 {
		return []int{0, 1}
	}

	results := make([]int, SECTIONS)

	//initialize the DP table
	table := make([][]float64, SECTIONS)
	bestPivots := make([][]int, SECTIONS)

	for i := 0; i < SECTIONS; i++ {
		table[i] = make([]float64, n)
		bestPivots[i] = make([]int, n)
	}

	//initialize the base case
	for i := 0; i < n; i++ {
		table[0][i] = model.sectionLogLike(bay, 0, 0, i+1)
		bestPivots[0][i] = 0
	}

	//compute the probabilities for the middle section
	//iterate over all possible endpoints
	//start at the section number to guarantee an image for the starting section
	for s := 1; s < SECTIONS; s++ {

		start := s

		//just skip all the intermediate calculations for the last section since all the images need to be used
		if s == MAX_SECTION {
			start = n - 1
		}

		//for each image in the bay calculate the probability of ending in the current state
		for i := start; i < n; i++ {

			bestProb := math.Inf(-1)
			bestIdx := s - 1

			//calculate the best transition point from the previous section
			//iterate over all possible intermediate cut-offs
			//start at the second number to guarantee enough images for previous sections
			for j := 1; j < i; j++ {
				prob := model.sectionLogLike(bay, s, j, i+1) + table[s-1][j-1] //j-1, since the table is inclusive, not exclusive

				if prob > bestProb {
					bestProb = prob
					bestIdx = j
				}
			}

			table[s][i] = bestProb
			bestPivots[s][i] = bestIdx
		}
	}

	//rewind the max-predictions to find the best split points
	//pick the best split point for the final section
	results[MAX_SECTION] = bestPivots[MAX_SECTION][n-1]
	results[MIDDLE] = bestPivots[MIDDLE][results[MAX_SECTION]-1]

	return results
}

// sectionLogLike computes the log-likelihood of a section of a bay i.e beginning, middle, or end
// the start index is include and the end is exclusive
func (model *BayModel) sectionLogLike(bay *Bay, sectionIdx int, start int, end int) float64 {
	countMean := model.count[sectionIdx]

	// the last bay has fewer vines, scale the expected mean accordingly
	if bay.bayNum == NUM_BAYS {
		countMean = scaleLast(countMean)
	}

	noPostCount, total := countPosts(bay.images, start, end)

	return PoissonLogProb(model.count[sectionIdx], total) + BinomialLogProb(total, noPostCount, model.composition[sectionIdx])
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

	var counts [SECTIONS]float64
	var props [SECTIONS]float64
	total := 0

	// average the number of empty images in all the bays and cameras
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < len(init[c]); i++ {
			for _, bay := range init[c][i].bays {

				partition := model.maxSectionAssignment(&bay)

				// for each section, estimate the number of images and the % of no-post images
				for s := 0; s < len(partition); s++ {
					end := -1

					//the last section gets all the remaining images
					if s == len(partition)-1 {
						end = len(bay.images) - 1
					} else {
						end = partition[s+1]
					}

					posts, numImages := countPosts(bay.images, partition[s], end)

					counts[s] += float64(numImages)
					props[s] += float64(posts) / float64(numImages)
					total++
				}
			}
		}
	}

	norm := float64(total) / SECTIONS

	//average the number of post images in all the bays
	for s := 0; s < SECTIONS; s++ {
		counts[s] = counts[s] / norm
		props[s] = props[s] / norm
	}

	model.count = counts
	model.composition = props
}

// countPosts returns the number non-posts and total images in a window
func countPosts(images []Image, start int, end int) (int, int) {
	noPosts := 0
	total := 0

	for i := start; i < end; i++ {
		if !images[i].hasPost {
			noPosts++
		}
		total++
	}

	return noPosts, total
}

// initialModel creates an initial model based on the
func initialModel(images []Image) BayModel {

	const STARTING_PROB = .9
	mean := float64(len(images)) / float64(NUM_ROWS*NUM_BAYS*CAMERAS*SECTIONS)

	probs := [SECTIONS]float64{1.0 - STARTING_PROB, STARTING_PROB, 1.0 - STARTING_PROB}
	counts := [SECTIONS]float64{mean, mean, mean}

	return BayModel{counts, probs}
}

// PoissonLogProb computes the log probability of a count under a Poisson distribution
func PoissonLogProb(lambda float64, count int) float64 {
	if count <= 0 {
		// use a very small probability instead of zero
		return EPS
	} else {
		// the numerator is lambda^k e^-lambda i.e. in log space: k ln lambda - lambda
		num := (float64(count) * math.Log(lambda)) - lambda
		denom := 0.0

		// the denominator is the sum of 1 to k i.e. the log of the factorial of the count
		for i := 1; i <= count; i++ {
			denom += math.Log(float64(i))
		}

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
