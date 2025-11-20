# Quick Start Guide

Get up and running with Solidity Vulnerability Scanner in minutes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/solidity-scanner.git
cd solidity-scanner

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Option 2: Install via pip (when published)

```bash
pip install solidity-scanner
```

## Basic Usage

### Scan a Single File

```bash
solscan scan MyContract.sol
```

### Scan a Directory

```bash
solscan scan ./contracts
```

### Generate Specific Report Format

```bash
# JSON only
solscan scan MyContract.sol --format json

# CSV only
solscan scan MyContract.sol --format csv

# Markdown only
solscan scan MyContract.sol --format markdown
```

### View Only Critical Findings

```bash
solscan scan MyContract.sol --critical-only
```

### Calculate Security Score

```bash
solscan score MyContract.sol
```

## Example Workflow

1. **Scan your contract**:
   ```bash
   solscan scan MyContract.sol
   ```

2. **Review the terminal output** for immediate feedback

3. **Check generated reports**:
   - `MyContract_report.json` - Machine-readable format
   - `MyContract_findings.csv` - Spreadsheet format
   - `MyContract_security_audit.md` - Professional audit report

4. **Fix vulnerabilities** based on recommendations

5. **Re-scan** to verify fixes:
   ```bash
   solscan scan MyContract.sol --critical-only
   ```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install solidity-scanner
      - run: solscan scan ./contracts --critical-only
        # Exit code 1 will fail the build if vulnerabilities found
```

### GitLab CI Example

```yaml
security_scan:
  image: python:3.11
  script:
    - pip install solidity-scanner
    - solscan scan ./contracts --format json
  artifacts:
    reports:
      junit: contract_report.json
```

## Common Use Cases

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
solscan scan $(git diff --cached --name-only --diff-filter=ACM | grep '\.sol$')
```

### Batch Scanning

```bash
# Scan all contracts in a directory
for file in contracts/*.sol; do
    echo "Scanning $file..."
    solscan scan "$file" --format json
done
```

### Integration with Other Tools

```bash
# Combine with jq for JSON processing
solscan scan MyContract.sol --format json | jq '.findings[] | select(.severity == "CRITICAL")'
```

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Review [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for Python API usage

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/solidity-scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/solidity-scanner/discussions)
- **Documentation**: See the [README.md](README.md)

## Troubleshooting

### "Command not found: solscan"

Make sure the package is installed:
```bash
pip install -e .
```

### "No contracts found"

Ensure your `.sol` file contains valid Solidity code with at least one contract definition.

### "Permission denied"

Check file permissions:
```bash
chmod +x $(which solscan)  # If installed globally
```

---

**Ready to scan?** Run `solscan scan examples/vulnerable.sol` to see it in action!

