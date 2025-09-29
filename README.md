# paircode
A pair of AI devs at your disposal that work on code-related problems.

# Plan

- uses langgraph react agents and a supervisor to manage the agents
- one agent focused on writing code, the other on writing tests
- both have access to the file system and can read and write files as well as listing files, but the supervisor manages this
- the coder writes code, the tester writes tests and runs them
- the supervisor manages the conversation and ensures they stay on task
- the coder and tester must agree on a test plan before writing code
- the coder and tester must agree on a definition of done before finishing
- the coder and tester must communicate clearly and effectively
