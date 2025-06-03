package main

import (
	"fmt"
	"math"
	"sync"
)

const NUM_CAMERAS = 4

var EPS = math.Log(0.00000000001)

type PostModel struct {
	postProb       float64 //the probability of a post being observed in a post state
	groupMean      float64 //the expected size of a group (mean of Gaussian)
	countThreshold int     //out of the 4 cameras, the number of posts required to count as a start/end of bay
	numGroups      int     //22 for Crawford-beck: 21 bays + 1 extra bookend
}

type Row struct {
	rowNum int
	images [][]Image //sequences of images per camera, i.e. indexed by camera, then image
}

// numImages return the number of images per camera
func (row *Row) numImages() int {
	return len(row.images[0])
}

type State struct {
	state int     //should start at 0
	score float64 //the likelihood of being in this state
	start int     //the timestep of the first image in the state, inclusive
	end   int     //the timestep of the last image in the state, inclusive
}

// newState creates a new state
func newState(stateNum int) State {
	state := State{state: stateNum, score: math.Inf(-1)}
	return state
}

// isPostGroup returns true if the group should only contain posts
func (state *State) isPostGroup() bool {
	//odd groups are post groups
	return state.state%2 == 0
}

// numImages returns the number of images per camera
func (state *State) numImages() int {
	return state.end - state.start + 1
}

// TODO check if I need to flip the bay number/position for even rows
// TODO need an option to NOT toggle direction and just increment row e.g. 1, 2, 3 instead of 1E, 1W, 3E etc
// dpAssignment
func (model *PostModel) dpAssignment(rows []Row) []CameraAssignment {

	//make an assignment per row
	results := make([]CameraAssignment, NUM_CAMERAS)

	for i := 0; i < NUM_CAMERAS; i++ {
		results[i] = make(CameraAssignment, len(rows))
	}
	var waitGroup sync.WaitGroup

	//re-arrange the assignments to make the Camera assignment format
	for r, row := range rows {

		waitGroup.Add(1)

		go func(rowIdx int, pRow Row) {
			defer waitGroup.Done()
			camRows := model.dpRowAssignment(pRow)

			for i, camRow := range camRows {
				results[i][rowIdx] = camRow
			}
		}(r, row)
	}

	waitGroup.Wait()

	return results
}

// dp_row_assignment produces an assignment of images to bays on a per-camera basis
func (model *PostModel) dpRowAssignment(row Row) []RowAssignment {

	//TODO remove
	for camIdx, camImgs := range row.images {

		ex := ""
		dir := ""
		cam := 0
		rowNum := row.rowNum

		if len(camImgs) > 0 {
			ex = camImgs[0].path
			dir = camImgs[0].direction
			cam = camImgs[0].cameraNum
			rowNum = camImgs[0].row
		}
		fmt.Printf("Row %d (%d) Camera %d num images %d e.g. %s dir %s camera %d\n", row.rowNum, rowNum, camIdx, len(camImgs), ex, dir, cam)
	}

	results := make([]RowAssignment, 0)

	//use viterbi to find the most likely sequence of states
	indexes := bayIndexes(model.viterbi(row))

	//for each camera build a row assignment
	for c := 0; c < NUM_CAMERAS; c++ {

		//make a sequence of bays for the current camera
		bays := make([]Bay, 0)

		for i := 0; i < len(indexes)-1; i++ {

			bayNum := i + 1

			//TODO this should be done somewhere else...
			//reverse the bay number for even rows
			if row.rowNum%2 == 0 {
				bayNum = len(indexes) - i - 1
			}

			bays = append(bays, makeBay(bayNum, indexes[i]+1, indexes[i+1], c, row.images))
		}

		results = append(results, RowAssignment{rowNum: row.rowNum, bays: bays})
	}

	return results
}

func makeBay(bayNum int, start int, end int, camera int, images [][]Image) Bay {

	camImages := images[camera]

	if end < len(camImages) {
		return Bay{bayNum: bayNum, images: camImages[start : end+1]}
	} else {
		return Bay{bayNum: bayNum, images: make([]Image, 0)}
	}
}

// bayIndexes creates a sequence of indices that mark the beginning and end of each bay
func bayIndexes(states []State) []int {

	results := make([]int, 0)

	//for the first bay use negative one as the starting index
	results = append(results, -1)

	//for each state after the first, use the middle of each post group as the boundary of the bays
	for i := 1; i < len(states)-1; i++ {
		if states[i].isPostGroup() {
			results = append(results, (states[i].start+states[i].end)/2)
		}
	}

	//put the max index on the end
	results = append(results, states[len(states)-1].end)

	return results
}

// viterbi predicts a state sequence for the given row starting at the beginning of the row
func (model *PostModel) viterbi(row Row) []State {

	//the DP table, the probability of being in each state at each timestep, i.e. time index, state index
	lattice := make([][]State, 0)
	startingStates := make([]State, 0)

	//base case for t=0
	for s := 0; s < model.numGroups; s++ {
		nextState := newState(s)

		//only calculate probability for the first state, no other state is allowed
		if s == 0 {
			//just the probability of observing the image in the state
			nextState.score = model.observationProb(row.images, 0, 0, nextState.isPostGroup())

		} else {
			nextState.score = math.Log(0) //should be negative infinity
		}

		startingStates = append(startingStates, nextState)
	}

	//add the initial states for t=0
	lattice = append(lattice, startingStates)

	//build the DP table
	//for each timestep in the row, compute the probability of being in each state
	for t := 0; t < row.numImages(); t++ {

		states := make([]State, model.numGroups)

		//for possible state compute the probability of ending up in it
		//P(S | o_1...o_i) = max_j P(S-1 | o_1...o_j) P(o_j...o_i | S) T(S-1, S | o_j...o_i)
		for s := 0; s < len(states); s++ {
			//general case, either transition from s-1 state or stay in the same state
			nextState := newState(s)
			nextState.end = t

			//set the previous best to negative infinity
			prevBestScore := math.Inf(-1)
			bestSplit := 0

			//for each "jump point" aka "split point" consider how many timesteps are optimal to have been in
			//the current state i.e. from j to t
			for j := s; j < t; j++ {

				//TODO remove
				//fmt.Printf("Looking back to %d at time %d in state %d ", j, t, s)

				var prev float64

				//special case for s=0, there no state to transition from
				if s > 0 {
					prev = lattice[j][s-1].score
				} else {
					prev = 0.0
				}

				//computes the probability of ending up in this state after seeing (t - j) images
				prevScore := prev + model.transitionProb(t-j) + model.observationProb(row.images, j, t, nextState.isPostGroup())

				//TODO remove
				//fmt.Println("prev score", prevScore)

				if prevScore > prevBestScore {
					prevBestScore = prevScore
					bestSplit = j
				}
			}

			//TODO remove
			//fmt.Printf("Best for %d (s) at %d (t) is %d (j) %.4f\n", s, t, bestSplit, prevBestScore)

			//set the score and the starting index for the state
			nextState.start = bestSplit
			nextState.score = prevBestScore

			states[s] = nextState
		}

		lattice = append(lattice, states)
	}

	n := len(lattice) - 1
	//optimal := lattice[n][1]
	optimal := lattice[n][model.numGroups-1]

	//determine the optimal final state
	/*for _, state := range lattice[n] {
		//TODO remove
		fmt.Println("state", state.state, state.score)

		//the state check is a hack because there is no transition probability so state=0 prob is inflated
		if state.score > optimal.score && state.state != 0 {
			optimal = state
		}
	}*/

	//TODO remove
	//fmt.Println("optimal", optimal)

	results := make([]State, 0)
	current := optimal
	results = append(results, current)

	//TODO remove
	//fmt.Println("start ", current)

	//add in all the prior states
	for current.state != 0 {

		next := current

		//jump back in time based on the number of images in the state
		for _, state := range lattice[current.start] {

			//TODO remove
			//fmt.Println("candidate", state.start-1, state)

			if state.state == current.state-1 && current.start-1 == state.end {
				next = state
				break
			}
		}

		//TODO REMOVE
		//fmt.Println("next", next)

		current = next
		results = append(results, current)
	}

	//reverse the sequence of states
	m := len(results) - 1
	for i := 0; i < len(results)/2; i++ {
		swap := results[i]
		results[i] = results[m-i]
		results[m-i] = swap
	}

	return results
}

// observationProb return the log probability of observing a post or no post in the given state
func (model *PostModel) observationProb(images [][]Image, start int, end int, isPostGroup bool) float64 {

	//make a slice of post counts for the window given
	counts := make([]int, end-start+1)

	//for each camera, count how many posts there are
	for i := 0; i < NUM_CAMERAS; i++ {
		countIndex := 0
		for c := start; c <= end && c < len(images[i]); c++ {
			if images[i][c].hasPost {
				counts[countIndex]++
			}
			countIndex++
		}
	}

	posts := 0
	noPosts := 0

	//count up the number of actual posts in the window
	for _, count := range counts {
		if count >= model.countThreshold {
			posts++
		} else {
			noPosts++
		}
	}

	//determine the probability of seeing a post based on the state
	postProb := 0.0

	if isPostGroup {
		postProb = model.postProb
	} else {
		postProb = 1.0 - model.postProb
	}

	noPostProb := 1.0 - postProb

	//calculate the log binomial probability based on the number of posts vs window size and the state
	//TODO refactor this... the args make no sense
	return BinomialLogProb(posts+noPosts, noPosts, noPostProb)
}

// transitionProb return the log probability of transitioning from the old state to the new one
func (model *PostModel) transitionProb(numImages int) float64 {
	//return math.Log(NormalCDF(float64(numImages), model.groupMean, model.groupStDev))
	return PoissonLogProb(model.groupMean, numImages)
}

// NormalCDF the cumulative density function of a Gaussian distribution
func NormalCDF(x, mean, stdDev float64) float64 {
	return 0.5 * (1 + math.Erf((x-mean)/(stdDev*math.Sqrt2)))
}

// LogSumExp calculates log(exp(logX) + exp(logY)) in a numerically stable way
func LogSumExp(logX, logY float64) float64 {
	// Handle edge cases
	if math.IsInf(logX, -1) {
		return logY
	}
	if math.IsInf(logY, -1) {
		return logX
	}

	// Find the maximum of logX and logY
	maxLog := math.Max(logX, logY)

	// Calculate log(exp(logX) + exp(logY)) using the log-sum-exp trick
	return maxLog + math.Log(math.Exp(logX-maxLog)+math.Exp(logY-maxLog))
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

// logFactorial computes the factorial but in log space
func logFactorial(n int) float64 {
	denom := 0.0
	for i := 1; i <= n; i++ {
		denom += math.Log(float64(i))
	}
	return denom
}
