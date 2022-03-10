package main

import (
  "example.com/greetings"
  "fmt"
  "log"
)

import "rsc.io/quote"

func main() {
  // Set properties of the predefined Logger, including
  // the log entry prefix and a flag to disable printing
  // the time, source file, and line number.
  log.SetPrefix("greetings: ")
  log.SetFlags(0)

  message, err := greetings.Hello("hi")

  if err != nil {
    log.Fatal(err)
  }

  fmt.Println(message)
  fmt.Println(quote.Go())
}
