# API Documentation

## Overview

This document provides comprehensive API documentation for Solidity Vulnerability Scanner. The scanner can be used both as a command-line tool and as a Python library.

## Command-Line Interface

### `solscan scan`

Scan Solidity files for vulnerabilities.

#### Usage

```bash
solscan scan <path> [options]
```

#### Arguments

- `path` (required): Path to Solidity file or directory containing `.sol` files

#### Options

- `--format {json,csv,markdown}`: Output format (default: all formats)
- `--critical-only`: Only show CRITICAL and HIGH severity findings

#### Examples

```bash
# Scan a single file
solscan scan MyContract.sol

# Scan a directory
solscan scan ./contracts

# Generate JSON report only
solscan scan MyContract.sol --format json

# Only critical findings
solscan scan MyContract.sol --critical-only
```

#### Exit Codes

- `0`: No critical/high vulnerabilities found
- `1`: Critical or high vulnerabilities detected

### `solscan score`

Calculate security score for a Solidity file.

#### Usage

```bash
solscan score <path>
```

#### Arguments

- `path` (required): Path to Solidity file

#### Examples

```bash
solscan score MyContract.sol
```

#### Output

```
Security Score for MyContract.sol: 75.0/100
Total Findings: 5

Breakdown:
  CRITICAL: 1
  HIGH: 2
  MEDIUM: 2
```

## Python API

### Core Modules

#### `solidity_scanner.parser`

##### `SolidityParser`

Main parser class for Solidity source code.

```python
from solidity_scanner.parser import SolidityParser
from pathlib import Path

parser = SolidityParser(source_code, file_path=Path("contract.sol"))
contracts = parser.parse()
```

**Methods**:

- `parse() -> List[ContractInfo]`: Parse source code and return contract information
- `get_external_calls(function_body: str, line_offset: int = 0) -> List[ExternalCall]`: Extract external calls
- `get_state_writes(function_body: str, state_variables: List[StateVariable]) -> List[Tuple[str, int]]`: Find state variable writes
- `has_require_check(function_body: str) -> bool`: Check for require() statements
- `get_hardcoded_addresses() -> List[Tuple[str, int]]`: Find hardcoded addresses

**Data Classes**:

- `ContractInfo`: Contract metadata
- `FunctionNode`: Function representation
- `StateVariable`: State variable representation
- `ExternalCall`: External call representation

#### `solidity_scanner.detectors`

##### `BaseDetector`

Base class for all vulnerability detectors.

```python
from solidity_scanner.detectors.base import BaseDetector, Finding

class MyDetector(BaseDetector):
    def detect(self, contracts, source_code, file_path):
        # Detection logic
        return self.findings
```

**Methods**:

- `detect(contracts: List[ContractInfo], source_code: str, file_path: str) -> List[Finding]`: Abstract method to detect vulnerabilities
- `add_finding(...)`: Add a finding to results

##### Available Detectors

- `ReentrancyDetector`: Detects reentrancy vulnerabilities
- `ValidationDetector`: Detects missing validation and unsafe arithmetic
- `BadPatternsDetector`: Detects anti-patterns and insecure practices
- `InsecureCallsDetector`: Detects unsafe call patterns

**Example**:

```python
from solidity_scanner.detectors import ReentrancyDetector
from solidity_scanner.parser import SolidityParser

parser = SolidityParser(source_code)
contracts = parser.parse()

detector = ReentrancyDetector()
findings = detector.detect(contracts, source_code, "contract.sol")

for finding in findings:
    print(f"{finding.severity}: {finding.title}")
```

#### `solidity_scanner.reporter`

##### `Reporter`

Report generation engine.

```python
from solidity_scanner.reporter import Reporter
from solidity_scanner.detectors.base import Finding

findings = [Finding(...), Finding(...)]
reporter = Reporter(findings, "contract.sol")

# Generate reports
reporter.print_terminal()
reporter.generate_json("report.json")
reporter.generate_csv("findings.csv")
reporter.generate_markdown("audit.md")

# Get exit code for CI/CD
exit_code = reporter.get_exit_code()
```

**Methods**:

- `print_terminal(critical_only: bool = False) -> None`: Print findings to terminal
- `generate_json(output_path: str) -> None`: Generate JSON report
- `generate_csv(output_path: str) -> None`: Generate CSV report
- `generate_markdown(output_path: str) -> None`: Generate Markdown audit report
- `get_exit_code(critical_only: bool = False) -> int`: Get exit code (0 or 1)

#### `solidity_scanner.utils`

Utility functions.

```python
from solidity_scanner.utils import find_solidity_files, read_file_content
from pathlib import Path

# Find all .sol files
sol_files = find_solidity_files("./contracts")

# Read file content
content = read_file_content(Path("contract.sol"))
```

**Functions**:

- `find_solidity_files(path: str) -> List[Path]`: Find all `.sol` files recursively
- `read_file_content(file_path: Path) -> Optional[str]`: Read file content with error handling
- `get_severity_color(severity: str) -> str`: Get ANSI color code for severity
- `format_code_snippet(lines: List[str], line_number: int, context: int = 3) -> str`: Format code snippet

## Usage Examples

### Basic Scanning

```python
from solidity_scanner.parser import SolidityParser
from solidity_scanner.detectors import (
    ReentrancyDetector,
    ValidationDetector,
    BadPatternsDetector,
    InsecureCallsDetector,
)
from solidity_scanner.reporter import Reporter
from solidity_scanner.utils import read_file_content
from pathlib import Path

# Read source code
file_path = Path("MyContract.sol")
source_code = read_file_content(file_path)

# Parse contract
parser = SolidityParser(source_code, file_path)
contracts = parser.parse()

# Run detectors
all_findings = []
detectors = [
    ReentrancyDetector(),
    ValidationDetector(),
    BadPatternsDetector(),
    InsecureCallsDetector(),
]

for detector in detectors:
    findings = detector.detect(contracts, source_code, str(file_path))
    all_findings.extend(findings)

# Generate report
reporter = Reporter(all_findings, str(file_path))
reporter.print_terminal()
reporter.generate_json("report.json")
```

### Custom Detector

```python
from solidity_scanner.detectors.base import BaseDetector, Finding
from solidity_scanner.parser import ContractInfo, FunctionNode
from typing import List

class CustomDetector(BaseDetector):
    """Custom detector example."""
    
    def detect(
        self,
        contracts: List[ContractInfo],
        source_code: str,
        file_path: str
    ) -> List[Finding]:
        """Detect custom vulnerability."""
        for contract in contracts:
            for func in contract.functions:
                # Custom detection logic
                if self._check_custom_pattern(func):
                    self.add_finding(
                        severity='MEDIUM',
                        title='Custom Vulnerability',
                        description='Description of the issue',
                        file_path=file_path,
                        line_number=func.line_start,
                        function_name=func.name,
                    )
        return self.findings
    
    def _check_custom_pattern(self, func: FunctionNode) -> bool:
        """Check for custom pattern."""
        # Implementation
        return False
```

### CI/CD Integration

```python
import sys
from solidity_scanner.cli import scan_file
from pathlib import Path

# Scan file
exit_code = scan_file(Path("MyContract.sol"), critical_only=True)

# Exit with code for CI/CD
sys.exit(exit_code)
```

## Data Structures

### `Finding`

Represents a security finding.

```python
@dataclass
class Finding:
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str             # Short title
    description: str       # Detailed description
    file_path: str         # Path to source file
    line_number: int       # Line number of issue
    function_name: str     # Function name (optional)
    code_snippet: str      # Code snippet (optional)
    recommendation: str   # Fix recommendation (optional)
    reference: str         # Reference links (optional)
```

### `ContractInfo`

Contract metadata.

```python
@dataclass
class ContractInfo:
    name: str                          # Contract name
    functions: List[FunctionNode]      # List of functions
    state_variables: List[StateVariable]  # List of state variables
    modifiers: List[str]               # List of modifier names
    line_start: int                    # Starting line number
    line_end: int                      # Ending line number
```

### `FunctionNode`

Function representation.

```python
@dataclass
class FunctionNode:
    name: str              # Function name
    visibility: str        # public, private, internal, external
    is_payable: bool       # Is payable function
    is_view: bool          # Is view function
    is_pure: bool          # Is pure function
    modifiers: List[str]    # List of modifiers
    line_start: int        # Starting line number
    line_end: int          # Ending line number
    body: str              # Function body
    parameters: List[str]  # Function parameters
    returns: List[str]     # Return types
```

## Error Handling

### Exceptions

- `FileNotFoundError`: File does not exist
- `PermissionError`: Cannot read file due to permissions
- `ValueError`: Invalid file or configuration
- `UnicodeDecodeError`: File cannot be decoded as UTF-8

### Example

```python
from solidity_scanner.utils import read_file_content
from pathlib import Path

try:
    content = read_file_content(Path("contract.sol"))
except FileNotFoundError:
    print("File not found")
except PermissionError:
    print("Permission denied")
except ValueError as e:
    print(f"Invalid file: {e}")
```

## Logging

The scanner uses Python's `logging` module.

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

# Logger names
# - solidity_scanner.parser
# - solidity_scanner.detectors.*
# - solidity_scanner.reporter
# - solidity_scanner.cli
```

## Performance Considerations

- **Parsing**: Single-pass parsing, results cached
- **Detection**: Detectors run independently (can be parallelized)
- **Memory**: File size limit of 10MB to prevent memory exhaustion
- **Scalability**: Suitable for small to medium projects; large projects may require optimization

## Limitations

1. **Regex Parsing**: Current parser uses regex, may not handle all Solidity syntax
2. **Static Analysis**: Only detects patterns, not runtime vulnerabilities
3. **False Positives**: Some findings may require manual verification
4. **Single File**: Currently analyzes one file at a time (imports not resolved)

## Future Enhancements

- Full AST parsing integration
- Multi-file contract analysis
- Import resolution
- Custom rule engine
- Automated fix suggestions

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0

