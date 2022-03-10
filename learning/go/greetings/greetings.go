package greetings

import (
	"errors"
	"fmt"
)

func Hello(name string) (string, error) {
	if name == "" {
		return "", errors.New("empty name")
	}
	// := is used for declaring and initializing in one line and is equivilent to
	// ```
	// var message string
	// message = ...
	// ```
	msg := fmt.Sprintf("Hi, %v. Welcome!", name)
	return msg, nil
}
