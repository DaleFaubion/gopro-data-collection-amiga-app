package main

import (
	"math"
	"testing"
)

func Test_LogProb_1(t *testing.T) {
	prob := PoissonLogProb(1, 1)

	if prob != -1.0 {
		t.Errorf("Log Poi. prob of 1 with lambda = 1 should be -1 but %f was calculated", prob)
	}
}

func Test_LogProb_2(t *testing.T) {
	const answer = 1.3068528194400546
	prob := PoissonLogProb(2, 1)

	if math.Abs(prob+answer) > 0.00001 {
		t.Errorf("Log Poi. prob of 2 with lambda = 1 should be -%f but %f was calculated", answer, prob)
	}
}

func Test_LogProb_lambda3_2(t *testing.T) {
	const answer = 1.4959226032237258
	prob := PoissonLogProb(3, 2)

	if math.Abs(prob+answer) > 0.00001 {
		t.Errorf("Log Poi. prob of 2 with lambda = 1 should be -%f but %f was calculated", answer, prob)
	}
}

func Test_LogBinomial(t *testing.T) {
	answer := math.Log(0.20132659199999978)

	prob := BinomialLogProb(10, 7, .8)

	if math.Abs(answer-prob) > 0.00001 {
		t.Errorf("Log Binomial 7 out of 10 with a prob of 0.8 should be %.4f but %.4f was calculated", answer, prob)
	}
}
