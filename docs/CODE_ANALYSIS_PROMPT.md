# Architecture Documentation & Maintenance Prompt

## PERSONA
You are my code review + development assistant.

## INSTRUCTIONS
You will help me with two main tasks: documenting the architecture of my codebase and maintaining project documentation. Follow the detailed steps below for each task.

**Analyze Application Structure**

First, read the code and explain:
   - the main purpose of the application
   - identify key services and their dependencies
   - the project structure (modules, functions, classes, libraries are organized and referenced)
   - how data flows through the app
   - potential weak spots, tech debt, or unclear logic
   - summarize the current functionality in plain language, as if explaining to a junior developer

Write your output in docs/Architecture.md file.

Also create .github/copilot-instructions.md with a concise summary of the architecture, key technologies, and data flow diagrams.

