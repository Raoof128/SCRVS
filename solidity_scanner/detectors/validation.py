"""
Input validation detector.

Detects missing input validation, uninitialized variables, and unsafe arithmetic.
"""

import re
from typing import List

from ..parser import ContractInfo, FunctionNode
from .base import BaseDetector, Finding


class ValidationDetector(BaseDetector):
    """Detects missing input validation and unsafe patterns."""

    def detect(
        self, contracts: List[ContractInfo], source_code: str, file_path: str
    ) -> List[Finding]:
        """
        Detect validation issues.

        Args:
            contracts: List of ContractInfo objects
            source_code: Full source code
            file_path: Path to the source file

        Returns:
            List of Finding objects
        """
        self.findings = []

        for contract in contracts:
            for func in contract.functions:
                # Check for missing require() checks
                self._check_missing_validation(func, file_path)

                # Check for unsafe arithmetic (if Solidity < 0.8)
                self._check_unsafe_arithmetic(func, source_code, file_path)

        # Check for hardcoded addresses
        self._check_hardcoded_addresses(source_code, file_path)

        return self.findings

    def _check_missing_validation(self, func: FunctionNode, file_path: str) -> None:
        """Check if function lacks input validation."""
        # Skip view/pure functions
        if func.is_view or func.is_pure:
            return

        # Check if function has parameters
        # Look for function signature with parameters (non-empty parentheses)
        # The function body includes the signature, so we can check for parameters there
        has_params = bool(re.search(r"function\s+\w+\s*\([^)]+\w+[^)]*\)", func.body))

        # Check if function has require() or revert()
        # Remove comments before checking
        body_without_comments = re.sub(r"//.*?$", "", func.body, flags=re.MULTILINE)
        body_without_comments = re.sub(r"/\*.*?\*/", "", body_without_comments, flags=re.DOTALL)
        has_validation = bool(re.search(r"(require|revert|assert)\s*\(", body_without_comments))

        # Check if function modifies state or makes external calls
        has_state_change = bool(re.search(r"=\s*[^=]|\.(call|send|transfer)\s*\(", func.body))

        if has_params and has_state_change and not has_validation:
            self.add_finding(
                severity="MEDIUM",
                title="Missing Input Validation",
                description=(
                    f"Function '{func.name}' accepts parameters and modifies state "
                    f"but lacks input validation checks. This could lead to unexpected behavior "
                    f"or exploitation."
                ),
                file_path=file_path,
                line_number=func.line_start,
                function_name=func.name,
                recommendation=(
                    f"Add require() statements to validate inputs in '{func.name}':\n"
                    'require(condition, "Error message");'
                ),
                reference=(
                    "https://consensys.github.io/smart-contract-best-practices/"
                    "development-recommendations/gas-optimization/"
                ),
            )

    def _check_unsafe_arithmetic(
        self, func: FunctionNode, source_code: str, file_path: str
    ) -> None:
        """Check for unsafe arithmetic operations."""
        # Check Solidity version
        version_match = re.search(r"pragma\s+solidity\s+([\d.]+)", source_code)
        if version_match:
            version = version_match.group(1)
            # Check if version >= 0.8.0 (has built-in overflow protection)
            try:
                major, minor = map(int, version.split(".")[:2])
                if major > 0 or (major == 0 and minor >= 8):
                    return  # Safe arithmetic in 0.8+
            except (ValueError, IndexError):
                pass

        # Look for arithmetic operations
        arithmetic_patterns = [
            (r"(\w+)\s*\+\s*(\w+)", "addition"),
            (r"(\w+)\s*-\s*(\w+)", "subtraction"),
            (r"(\w+)\s*\*\s*(\w+)", "multiplication"),
        ]

        for pattern, op_type in arithmetic_patterns:
            matches = re.finditer(pattern, func.body)
            for match in matches:
                # Check if it's not in a require/assert (which might be checking overflow)
                context_before = func.body[: match.start()]
                if "require" not in context_before[-50:] and "assert" not in context_before[-50:]:
                    line_num = func.line_start + func.body[: match.start()].count("\n")

                    self.add_finding(
                        severity="MEDIUM",
                        title=f"Potential Integer Overflow/Underflow: {op_type.title()}",
                        description=(
                            f"Function '{func.name}' performs {op_type} operation "
                            f"without overflow checks. "
                            f"In Solidity < 0.8.0, arithmetic operations can "
                            f"overflow/underflow silently."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        function_name=func.name,
                        recommendation=(
                            "Use SafeMath library or upgrade to Solidity >= 0.8.0:\n"
                            "// Solidity >= 0.8.0 has built-in overflow protection\n"
                            "pragma solidity ^0.8.0;"
                        ),
                        reference=(
                            "https://consensys.github.io/smart-contract-best-practices/"
                            "development-recommendations/solidity-specific/"
                            "integer-arithmetic/"
                        ),
                    )
                    break

    def _check_hardcoded_addresses(self, source_code: str, file_path: str) -> None:
        """Check for hardcoded Ethereum addresses."""
        # Pattern: 0x followed by 40 hex characters
        address_pattern = r"0x[a-fA-F0-9]{40}"
        lines = source_code.split("\n")

        for i, line in enumerate(lines, 1):
            matches = re.finditer(address_pattern, line)
            for match in matches:
                address = match.group(0)
                # Skip if it's in a comment
                if "//" in line[: match.start()] or "/*" in line[: match.start()]:
                    continue

                self.add_finding(
                    severity="LOW",
                    title="Hardcoded Address",
                    description=(
                        f"Hardcoded address found: {address}. Hardcoded addresses reduce "
                        f"flexibility and make contracts harder to maintain. Consider using "
                        f"configuration variables or constructor parameters."
                    ),
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line.strip(),
                    recommendation=(
                        "Use a state variable or constructor parameter:\n"
                        "address public constant ADMIN = 0x...; // or\n"
                        "constructor(address _admin) { admin = _admin; }"
                    ),
                    reference=(
                        "https://consensys.github.io/smart-contract-best-practices/"
                        "development-recommendations/general/external-calls/"
                    ),
                )
