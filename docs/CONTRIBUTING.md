# Contributing to Merlai

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker (optional)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-username/Merlai.git
cd Merlai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
flake8 merlai/
black --check merlai/
mypy merlai/
```

## Pull Request Guidelines

### Code Changes

For code changes (Python files, tests, scripts), the full CI pipeline will run:
- Linting (flake8)
- Type checking (mypy)
- Format checking (black)
- Unit tests (pytest)
- Docker build

### Documentation Changes

For documentation changes only (`.md`, `.txt`, `docs/`, `README`, `CHANGELOG`), add the `documentation` label to your PR to run only a quick format check:

1. Create your PR as usual
2. Add the `documentation` label to your PR
3. Only a quick format check will run (much faster!)

**Supported documentation files:**
- `.md` files (Markdown)
- `.txt` files (Text)
- `.rst` files (reStructuredText)
- Files in `docs/` directory
- `README.md`, `CHANGELOG.md`, `LICENSE`, `NOTICE`

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(api): add MIDI generation endpoint
fix(core): resolve memory leak in music processing
docs(readme): update installation instructions
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=merlai

# Run with verbose output
pytest -v
```

### Test Structure

- `tests/test_api.py`: API endpoint tests
- `tests/test_core.py`: Core functionality tests
- `tests/test_cli.py`: CLI command tests
- `tests/test_integration.py`: Integration tests

## Code Style

### Python

We use:
- **Black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **isort** for import sorting

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run formatting and linting on commit.

## Docker Development

### Build Images

```bash
# Build lightweight image
docker build -f docker/Dockerfile.lightweight -t merlai:lightweight .

# Build GPU image
docker build -f docker/Dockerfile.gpu -t merlai:gpu .
```

### Run with Docker

```bash
# Run lightweight version
docker run -p 8000:8000 merlai:lightweight

# Run GPU version
docker run --gpus all -p 8000:8000 merlai:gpu
```

## CI/CD Pipeline

### Pipeline Stages

1. **Quick Check** (documentation changes only)
   - Format check with Black

2. **Full Pipeline** (code changes)
   - Linting (flake8)
   - Type checking (mypy)
   - Format checking (black)
   - Unit tests (pytest)
   - Docker build

### Pipeline Optimization

- Documentation changes run only quick format check (~30 seconds)
- Code changes run full pipeline (~5-10 minutes)
- Manual workflow dispatch always runs full pipeline

## Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Slack**: Join our Slack channel for real-time chat

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a release tag: `git tag v1.0.0`
4. Push the tag: `git push origin v1.0.0`
5. GitHub Actions will automatically create a release

---

Thank you for contributing to Merlai! 🎵 