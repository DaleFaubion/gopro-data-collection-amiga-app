package main

import (
	"fmt"
	"math"
)

type Model interface {
	ExpectedModel(init []CameraAssignment)
	RowLogLikelihood(row *RowAssignment) float64
	Show()
}

//TODO make a non-probability model i.e. penalties for mismatching bays, missing starting or ending posts, etc

type DPModel struct {
	count       [SECTIONS]float64
	composition [SECTIONS]float64
}

type PoissonModel struct {
	startLambda float64
	imageLambda float64
	endLambda   float64
	noPostProb  float64
}

const SECTIONS = 3
const MAX_SECTION = 2
const VINES_PER_BAY = 5.0
const LAST_BAY_VINES = 4.0

var EPS = math.Log(0.00000000001)

func NewDPModel(mean float64, noPostProb float64) DPModel {
	means := [SECTIONS]float64{mean, mean, mean}
	probs := [SECTIONS]float64{1.0 - noPostProb, noPostProb, 1.0 - noPostProb}

	return DPModel{means, probs}
}

func scaleLast(mean float64) float64 {
	return (mean / VINES_PER_BAY) * LAST_BAY_VINES
}

// RowLogLikelihood computes the likelihood of the row ent
func (model *PoissonModel) RowLogLikelihood(row *RowAssignment) float64 {

	like := 0.0

	for i, bay := range row.bays {

		// scale down the expected images for the last bay
		startMean := model.startLambda
		middleMean := model.imageLambda
		endMean := model.endLambda

		if i == NUM_BAYS-1 {
			startMean = scaleLast(startMean)
			middleMean = scaleLast(middleMean)
			endMean = scaleLast(endMean)
		}

		start, end := bay.NumPosts()
		middle := bay.MiddlePosts()

		// compute the probability of the regular images
		reg := sectionLogLikelihood(middleMean, model.noPostProb, bay.NumEmpty()-middle, bay.NumImages())

		// compute the probability of the post images
		startLike := PoissonLogProb(startMean, start)

		endLike := PoissonLogProb(endMean, end)

		like += reg + startLike + endLike
	}

	return like
}

// RowLogLikelihood computes the likelihood of the row ent
func (model *DPModel) RowLogLikelihood(row *RowAssignment) float64 {

	like := 0.0

	for _, bay := range row.bays {

		if bay.NumImages() > 0 {
			partition := model.maxSectionAssignment(&bay)
			like += model.bayLogLikelihood(&bay, partition)
		}
	}

	return like
}

// bayLogLikelihood computes the log likelihood of the bay, give then partition of the images
func (model *DPModel) bayLogLikelihood(bay *Bay, partition []int) float64 {
	like := 0.0

	// add the end of the bay as the final endpoint
	partition = append(partition, bay.NumImages())

	for i := 0; i < len(partition)-1; i++ {
		like += model.sectionLogLike(bay, i, partition[i], partition[i+1])
	}

	return like
}

// maxSectionAssignment computes the assignment of images to sections (0,1,2) (start, middle, end)
// using a dynamic program (forward-pass HMM-like algorithm)
// the partition array return
func (model *DPModel) maxSectionAssignment(bay *Bay) []int {
	const MIDDLE = 1
	n := bay.NumImages()

	// early exit for special cases
	if n == 0 {
		return []int{}
	} else if n == 1 {
		return []int{0, 1}
	}

	results := make([]int, SECTIONS)

	//do the backwards pass
	back := model.backwardsPass(bay)

	//initialize the DP table
	forward := make([][]float64, SECTIONS)
	bestPivots := make([][]int, SECTIONS)

	for i := 0; i < SECTIONS; i++ {
		forward[i] = make([]float64, n)
		bestPivots[i] = make([]int, n)
	}

	//initialize the base case
	for i := 0; i < n; i++ {
		forward[0][i] = model.sectionLogLike(bay, 0, 0, i+1)
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
		//start 'i' at the section index since at least one image is needed for each section
		for i := start; i < n; i++ {

			bestProb := math.Inf(-1)
			bestIdx := s - 1

			//calculate the best transition point from the previous section
			//iterate over all possible intermediate cut-offs
			//start at the second number to guarantee enough images for previous sections
			for j := s; j < i; j++ {
				//j-1, since the table is inclusive, not exclusive
				prob := model.sectionLogLike(bay, s, j, i+1) + forward[s-1][j-1]

				//include the backwards prob, if there are images remaining in the sequence
				if i+1 < n {
					prob += back[s+1][i+1]
				}

				if prob > bestProb {
					bestProb = prob
					bestIdx = j
				}
			}

			forward[s][i] = bestProb
			bestPivots[s][i] = bestIdx
		}
	}

	//rewind the max-predictions to find the best split points
	//pick the best split point for the final section
	results[MAX_SECTION] = bestPivots[MAX_SECTION][n-1]
	results[MIDDLE] = bestPivots[MIDDLE][results[MAX_SECTION]-1]

	return results
}

// backwardsPass does an HMM-like backwards pass to compute the log-probability of being in a given section (state)
// after seeing some images
func (model *DPModel) backwardsPass(bay *Bay) [][]float64 {

	const LAST = 2

	n := bay.NumImages()
	table := make([][]float64, SECTIONS)

	//initialize the table for each section
	for i := 0; i < len(table); i++ {
		table[i] = make([]float64, n)
	}

	//initialize the DP table, covers the first section/state
	for i := n - 1; i >= 0; i-- {
		table[LAST][i] = model.sectionLogLike(bay, LAST, i, n)
	}

	//go through the sequence of images backwards, computing the probability of being in each section
	//minus 2 because of the off by one nature of indices and because we want to start in the second state
	for s := SECTIONS - 2; s >= 0; s-- {

		start := n - 2

		//for the last section, only the probability of the final image needs to be calculated
		if s == 0 {
			start = 0
		}

		//for each image find the probability of ending in section 's' after seeing image 'i'
		for i := start; i >= 0; i-- {

			bestProb := math.Inf(-1)

			//calculate the best transition point from the previous section
			//iterate over all possible intermediate cut-offs
			//start at the second number to guarantee enough images for previous sections
			for j := n - 2 - s; j > i; j-- {
				prob := model.sectionLogLike(bay, s, i, j+1) + table[s+1][j+1]

				if prob > bestProb {
					bestProb = prob
				}
			}

			table[s][i] = bestProb
		}
	}

	return table
}

// sectionLogLike computes the log-likelihood of a section of a bay i.e beginning, middle, or end
// the start index is include and the end is exclusive
func (model *DPModel) sectionLogLike(bay *Bay, sectionIdx int, start int, end int) float64 {
	countMean := model.count[sectionIdx]

	// the last bay has fewer vines, scale the expected mean accordingly
	if bay.bayNum == NUM_BAYS {
		countMean = scaleLast(countMean)
	}

	noPostCount, total := countPosts(bay.images, start, end)

	return sectionLogLikelihood(model.count[sectionIdx], model.composition[sectionIdx], noPostCount, total)
}

// LogLikelihood computes the score for the whole ent
func logLikelihood(model Model, rows CameraAssignment) float64 {
	like := 0.0

	for _, row := range rows {
		like += model.RowLogLikelihood(&row)
	}

	return like
}

// vineyardLogLikelihood computes the log-likelihood over the whole vineyard assignment
func vineyardLogLikelihood(model Model, vineyard []CameraAssignment) float64 {
	like := 0.0

	for _, assignment := range vineyard {
		like += logLikelihood(model, assignment)
	}

	return like
}

// em runs the expectation maximization algorithm to find the best row ent
func em(model Model, init []CameraAssignment, rounds int) []CameraAssignment {

	improved := true
	i := 0
	best := init
	bestLike := vineyardLogLikelihood(model, init)

	fmt.Printf("Starting likelihood: %.4f\n", bestLike)

	// for a fixed number of iterations, run the EM algo
	for i < rounds && improved {

		var next []CameraAssignment

		// for each camera, produce the best assignment
		for j := 0; j < CAMERAS; j++ {
			next = append(next, maxAssignment(model, best[j]))
		}

		// estimate the model parameters
		model.ExpectedModel(next)

		currentLike := vineyardLogLikelihood(model, next)

		fmt.Printf("Round %2d likelihood %.4f\n", i, currentLike)
		model.Show()
		fmt.Println()

		//only keep the changes if it is an improvement
		if currentLike > bestLike {
			best = next
			bestLike = currentLike
		} else {
			improved = false
		}

		i++
	}

	fmt.Printf("Best Round %d: %.4f\n", i-2, bestLike)

	return best
}

// maxAssignment create the maximum likelihood assignment of images under the current model
func maxAssignment(model Model, assignment CameraAssignment) CameraAssignment {
	var newRows []RowAssignment

	for _, row := range assignment {
		newRows = append(newRows, maxRow(model, row))
	}

	return newRows
}

// maxRow find the row that maximizes the likelihood under the current model
func maxRow(model Model, row RowAssignment) RowAssignment {

	done := false
	best := row
	bestScore := model.RowLogLikelihood(&best)

	// until there is no improvement, greedily try different candidates
	for !done {

		done = true

		// generate a collection of candidates
		candidates := best.generateAssignments()

		// evaluate all the candidates and pick the best
		for _, candidate := range candidates {

			score := model.RowLogLikelihood(&candidate)

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

// ExpectedModel updates the models parameters based on the current assignment
func (model *PoissonModel) ExpectedModel(init []CameraAssignment) {

	avgEmpty := 0.0
	avgStart := 0.0
	avgEnd := 0.0
	avgNoPost := 0.0
	total := 0

	// average the number of empty images in all the bays and cameras
	for c := 0; c < CAMERAS; c++ {
		for i := 0; i < len(init[c]); i++ {
			for _, bay := range init[c][i].bays {
				start, end := bay.NumPosts()
				avgEmpty += float64(bay.NumEmpty())
				avgStart += float64(start)
				avgEnd += float64(end)
				if bay.NumEmpty() > 0 {
					avgNoPost += float64(bay.NumEmpty()-bay.MiddlePosts()) / float64(bay.NumEmpty())
				}
				total += 1
			}
		}
	}

	//average the number of post images in all the bays
	model.imageLambda = avgEmpty / float64(total)
	model.startLambda = avgStart / float64(total)
	model.endLambda = avgEnd / float64(total)
	model.noPostProb = avgNoPost / float64(total)
}

// ExpectedModel updates the models parameters based on the current ent
func (model *DPModel) ExpectedModel(init []CameraAssignment) {

	var counts [SECTIONS]float64
	var props [SECTIONS]float64
	total := 0

	// average the number of empty images in all the bays and cameras
	for c := 0; c < len(init); c++ {
		for i := 0; i < len(init[c]); i++ {
			for _, bay := range init[c][i].bays {

				partition := model.maxSectionAssignment(&bay)

				// for each section, estimate the number of images and the % of no-post images
				for s := 0; s < len(partition); s++ {
					end := -1

					//the last section gets all the remaining images
					if s == len(partition)-1 {
						end = len(bay.images)
					} else {
						end = partition[s+1]
					}

					noPosts, numImages := countPosts(bay.images, partition[s], end)

					counts[s] += float64(numImages)

					if numImages > 0 {
						props[s] += float64(noPosts) / float64(numImages)
					}
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
func initialDPModel(images []Image) DPModel {

	const STARTING_PROB = .9
	mean := float64(len(images)) / float64(NUM_ROWS*NUM_BAYS*CAMERAS*SECTIONS)

	probs := [SECTIONS]float64{1.0 - STARTING_PROB, STARTING_PROB, 1.0 - STARTING_PROB}
	//counts := [SECTIONS]float64{mean, mean, mean}
	counts := [SECTIONS]float64{1.0, mean, 1.0}

	return DPModel{counts, probs}
}

// initialModel creates an initial model based on the
func initialPoissonModel(images []Image) PoissonModel {

	const NO_POST_INIT = .9

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
	return PoissonModel{postLambda, emptyLambda, postLambda, NO_POST_INIT}
}

// Show prints off the model's parameters
func (model *DPModel) Show() {
	fmt.Println("DP Bay Model")

	for s := 0; s < len(model.composition); s++ {
		fmt.Printf("Section %d: mean %.4f, prop %.4f\n", s, model.count[s], model.composition[s])
	}
}

// Show prints off the model's parameters
func (model *PoissonModel) Show() {
	fmt.Printf("Poisson Bay Model\n")
	fmt.Printf("Params: %.4f, Middle: %.4f, Prob: %.4f, End: %.4f\n", model.startLambda, model.imageLambda, model.noPostProb, model.endLambda)
}

// sectionLogLikelihood combines the poisson and binomial distributions to model both count and composition of
// each section
func sectionLogLikelihood(mean float64, noPostProb float64, noPostCount int, total int) float64 {
	return PoissonLogProb(mean, total) + BinomialLogProb(total, noPostCount, noPostProb)
}
