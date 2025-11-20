# Contributing to Solidity Vulnerability Scanner

First off, thank you for considering contributing to Solidity Vulnerability Scanner! It's people like you that make this project better.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots and animated GIFs if applicable**
- **Include the Solidity code that triggered the issue**
- **Include the scanner version and Python version**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Ensure code follows style guidelines (`black .`, `flake8 .`)
7. Commit your changes (`git commit -m 'Add some amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/solidity-scanner.git
   cd solidity-scanner
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines. We use:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run these tools before committing:

```bash
black solidity_scanner tests
isort solidity_scanner tests
flake8 solidity_scanner tests
mypy solidity_scanner
```

### Type Hints

All functions and methods must include type hints:

```python
def scan_file(file_path: Path, output_format: str | None = None) -> int:
    """Scan a Solidity file for vulnerabilities."""
    ...
```

### Docstrings

All public functions, classes, and modules must have docstrings following Google style:

```python
def detect_reentrancy(
    contracts: List[ContractInfo],
    source_code: str
) -> List[Finding]:
    """
    Detect reentrancy vulnerabilities in contracts.
    
    Args:
        contracts: List of parsed contract information
        source_code: Full source code of the contract
        
    Returns:
        List of Finding objects representing detected vulnerabilities
        
    Raises:
        ValueError: If contracts list is empty
    """
    ...
```

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add support for Solidity 0.9.0 syntax
fix: correct CEI violation detection logic
docs: update README with new usage examples
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=solidity_scanner --cov-report=html

# Run specific test file
pytest tests/test_reentrancy.py

# Run specific test
pytest tests/test_reentrancy.py::TestReentrancyDetector::test_detect_reentrancy_vulnerability
```

### Writing Tests

- Tests should be in the `tests/` directory
- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Mock external dependencies when appropriate

Example:

```python
def test_detect_reentrancy_vulnerability():
    """Test detection of reentrancy vulnerability."""
    source = """
    contract Vulnerable {
        function withdraw(uint256 amount) public {
            msg.sender.call{value: amount}("");
            balances[msg.sender] -= amount;
        }
    }
    """
    # Test implementation
    ...
```

## Adding New Detectors

To add a new vulnerability detector:

1. Create a new file in `solidity_scanner/detectors/`
2. Inherit from `BaseDetector`
3. Implement the `detect()` method
4. Add the detector to `solidity_scanner/detectors/__init__.py`
5. Register it in `cli.py`
6. Add tests in `tests/test_*.py`

Example:

```python
from .base import BaseDetector, Finding
from ..parser import ContractInfo

class MyDetector(BaseDetector):
    """Detects my specific vulnerability."""
    
    def detect(
        self,
        contracts: List[ContractInfo],
        source_code: str,
        file_path: str
    ) -> List[Finding]:
        """Detect vulnerabilities."""
        # Implementation
        return self.findings
```

## Documentation

- Update README.md if adding new features
- Add docstrings to all public functions
- Update CHANGELOG.md with your changes
- Include examples in docstrings when helpful

## Questions?

Feel free to open an issue for any questions about contributing. We're happy to help!

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing! 🎉

