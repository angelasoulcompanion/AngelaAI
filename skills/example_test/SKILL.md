# Skill: example_test

## Description
Example skill for testing the skills system. Says hello with a timestamp.

## Triggers
- schedule: every 4 hours
- command: /example

## Tools
- say_hello: Say hello with a greeting message
  - parameters: {name: string}
  - handler: handler.py::say_hello
- get_time: Get current time
  - parameters: {}
  - handler: handler.py::get_time

## Config
- greeting: Hello from Angela!
- language: en
