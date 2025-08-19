# GitGuard Rules Pack

## Determinism
- Temperature: 0.2
- Top P: 1.0
- Prefer minimal diffs
- Never invent APIs

## Safety & Policy
- Follow OPA/rego policy hints
- When a gate trips, include:
  - Input data
  - Rule context
  - Fix suggestions
- No new runtime dependencies without justification
- Prefer stdlib over external libraries
- Call out risky subprocess or shell usage

## Tests-First Discipline
- When modifying logic, write/adjust tests first
- Refuse to commit changes without passing tests
- Test coverage must not decrease

## Documentation & Developer Experience
- Public functions need docstrings
- Update README/CHANGELOG on externally visible changes
- Keep imports sorted
- Remove dead code
- Maintain clean git history

## Style Guidelines
- **Python**: Black + Ruff formatting; MyPy strict type checking
- **Line Length**: 100 characters maximum
- **Import Organization**: Use isort with Black profile
- **Code Quality**: Follow PEP 8 and PEP 257 conventions

## File Patterns
- Configuration files: `pyproject.toml`, `Makefile`, `.vscode/`
- Source code: `apps/`, `policies/`, `tests/`
- Documentation: `docs/`, `README.md`, `CHANGELOG.md`

## Workflow
1. Plan the change
2. Write/update tests
3. Implement minimal patch
4. Verify tests pass
5. Update documentation if needed
6. Stage in sequential commits for multi-file changes
