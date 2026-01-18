# Repository Guidelines

## Project Structure & Module Organization
This repository is currently minimal and contains only top-level documentation and licensing files.
- `README.md` holds the project description.
- `LICENSE` contains the license text.
If you add source code, organize it under clear top-level directories (for example, `src/` for code and `tests/` for test files) and update this guide accordingly.

## Build, Test, and Development Commands
No build, test, or run scripts are defined yet.
- If you add tooling, document the exact commands here (for example, `npm run build`, `npm test`, or `make dev`).
- Keep commands runnable from the repository root and note any required environment variables.

## Coding Style & Naming Conventions
There are no established coding standards in the repository yet.
- When adding code, choose a consistent style guide (for example, a formatter like Prettier or Black) and document it here.
- Use consistent naming patterns across files and folders (for example, `snake_case` for scripts or `PascalCase` for classes) once a language is chosen.

## Testing Guidelines
Testing frameworks and coverage requirements are not defined.
- If tests are added, prefer a single test framework per language and place tests in a dedicated `tests/` (or language-specific) directory.
- Document the test command and naming pattern (for example, `*_test.py` or `*.spec.ts`).

## Commit & Pull Request Guidelines
There is not enough Git history to infer commit conventions (the only commit message is "Initial commit").
- Use concise, present-tense commit messages (for example, "Add data ingestion script").
- For pull requests, include a short summary, testing notes, and any relevant screenshots or logs.

## Security & Configuration Tips
No secrets or configuration files are currently present.
- If you add configuration, store secrets in environment variables and document required keys in `README.md`.
- Do not commit API keys or credentials to the repository.
