# Contributing

Thank you for considering contributing to this project. This is one of the Manta open-source CLI tools — a collection of zero-dependency Python utilities built for reliability and portability.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/REPO_NAME.git`
3. Run the tests: `python -m pytest -v`

## Development Guidelines

- **Zero external dependencies.** The entire point of these tools is that they work with nothing but Python stdlib. No `requirements.txt`, no `pip install` beyond the tool itself.
- **Tests required.** Every feature needs a test. Run `python -m pytest` before committing.
- **Portable.** Must work on macOS, Linux, and WSL. No platform-specific code without a fallback.
- **Error messages tell you what to do.** Not just "error: invalid input" but "error: invalid input — expected a file path, got '--flag'."
- **Consistent exit codes.** 0 for success, 1 for user error, 2 for system error.

## Code Style

- Follow PEP 8
- Use `argparse` for CLI (not click, not typer — zero deps)
- Type hints on all function signatures
- Docstrings on public functions

## Pull Request Process

1. Update tests to cover your changes
2. Run the full test suite
3. Update the README if you changed CLI behavior
4. Submit the PR with a clear description of what changed and why

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
