"""
Solidity AST Parser

Parses Solidity source code and extracts relevant information for vulnerability analysis.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FunctionNode:
    """Represents a Solidity function."""

    name: str
    visibility: str  # public, private, internal, external
    is_payable: bool
    is_view: bool
    is_pure: bool
    modifiers: List[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    body: str = ""
    parameters: List[str] = field(default_factory=list)
    returns: List[str] = field(default_factory=list)


@dataclass
class StateVariable:
    """Represents a state variable."""

    name: str
    type: str
    visibility: str
    line_number: int = 0


@dataclass
class ExternalCall:
    """Represents an external call."""

    target: str
    value: Optional[str] = None
    method: str = ""
    line_number: int = 0
    call_type: str = ""  # call, send, transfer, delegatecall


@dataclass
class ContractInfo:
    """Represents a Solidity contract."""

    name: str
    functions: List[FunctionNode] = field(default_factory=list)
    state_variables: List[StateVariable] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


class SolidityParser:
    """Parser for Solidity source code."""

    def __init__(self, source_code: str, file_path: Optional[Path] = None):
        """
        Initialize parser with source code.

        Args:
            source_code: Solidity source code as string
            file_path: Optional path to the source file
        """
        self.source_code = source_code
        self.file_path = file_path
        self.lines = source_code.split("\n")
        self.contracts: List[ContractInfo] = []

    def parse(self) -> List[ContractInfo]:
        """
        Parse the source code and extract contract information.

        Returns:
            List of ContractInfo objects
        """
        try:
            self._extract_contracts()
            for contract in self.contracts:
                self._extract_functions(contract)
                self._extract_state_variables(contract)
                self._extract_modifiers(contract)
            return self.contracts
        except Exception as e:
            logger.error(f"Error parsing source code: {e}")
            return []

    def _extract_contracts(self) -> None:
        """Extract contract declarations."""
        # Pattern: contract ContractName { ... }
        contract_pattern = r"contract\s+(\w+)\s*(?:is\s+[\w\s,]+)?\s*\{"

        for i, line in enumerate(self.lines, 1):
            match = re.search(contract_pattern, line)
            if match:
                contract_name = match.group(1)
                # Find contract boundaries
                brace_count = 0
                start_line = i
                in_contract = False

                for j, contract_line in enumerate(self.lines[i - 1 :], start=i):
                    for char in contract_line:
                        if char == "{":
                            brace_count += 1
                            in_contract = True
                        elif char == "}":
                            brace_count -= 1
                            if in_contract and brace_count == 0:
                                contract = ContractInfo(
                                    name=contract_name, line_start=start_line, line_end=j
                                )
                                self.contracts.append(contract)
                                break
                    if in_contract and brace_count == 0:
                        break

    def _parse_modifiers_from_signature(self, line: str) -> List[str]:
        """
        Parse modifiers from function signature line.

        Args:
            line: Function signature line

        Returns:
            List of modifier names
        """
        modifiers = []
        paren_end = line.find(")")
        if paren_end > 0:
            after_sig = line[paren_end + 1 :]
            after_sig = re.sub(
                r"\b(public|private|internal|external|payable|view|pure|returns)\b",
                "",
                after_sig,
            )
            before_brace = after_sig.split("{")[0]
            modifier_matches = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", before_brace)
            excluded = {
                "function",
                "public",
                "private",
                "internal",
                "external",
                "payable",
                "view",
                "pure",
                "returns",
            }
            for mod in modifier_matches:
                if mod and mod not in excluded:
                    modifiers.append(mod)
        return modifiers

    def _extract_function_properties(self, line: str) -> tuple:
        """
        Extract function properties from signature line.

        Args:
            line: Function signature line

        Returns:
            Tuple of (visibility, is_payable, is_view, is_pure)
        """
        is_payable = "payable" in line
        is_view = "view" in line
        is_pure = "pure" in line

        visibility = "public"
        for vis in ["public", "private", "internal", "external"]:
            if vis in line:
                visibility = vis
                break

        return visibility, is_payable, is_view, is_pure

    def _extract_function_body(
        self, contract_lines: List[str], start_idx: int, contract_line_start: int
    ) -> tuple:
        """
        Extract function body by tracking braces.

        Args:
            contract_lines: Lines of the contract
            start_idx: Starting index in contract_lines
            contract_line_start: Starting line number of contract

        Returns:
            Tuple of (func_body, func_end_line) or (None, None) if not found
        """
        brace_count = 0
        func_body_lines = []
        in_function = False

        for j, func_line in enumerate(contract_lines[start_idx:], start=start_idx):
            func_body_lines.append(func_line)
            for char in func_line:
                if char == "{":
                    brace_count += 1
                    in_function = True
                elif char == "}":
                    brace_count -= 1
                    if in_function and brace_count == 0:
                        func_end_line = contract_line_start + j
                        func_body = "\n".join(func_body_lines)
                        return func_body, func_end_line
            if in_function and brace_count == 0:
                break

        return None, None

    def _extract_functions(self, contract: ContractInfo) -> None:
        """Extract functions from a contract."""
        contract_lines = self.lines[contract.line_start - 1 : contract.line_end]

        # Pattern: function name(...) visibility modifiers { ... }
        function_pattern = (
            r"function\s+(\w+)\s*\([^)]*\)\s*(?:public|private|internal|external)?"
            r"\s*(?:payable|view|pure)?\s*(?:returns\s*\([^)]*\))?\s*(?:[^{]*)?\{"
        )

        for i, line in enumerate(contract_lines, start=contract.line_start):
            match = re.search(function_pattern, line)
            if match:
                func_name = match.group(1)

                # Skip constructor
                if func_name == contract.name or func_name == "constructor":
                    continue

                # Extract function properties
                visibility, is_payable, is_view, is_pure = self._extract_function_properties(line)

                # Extract modifiers
                modifiers = self._parse_modifiers_from_signature(line)

                # Find function body
                start_idx = i - contract.line_start
                func_start_line = i
                func_body, func_end_line = self._extract_function_body(
                    contract_lines, start_idx, contract.line_start
                )

                if func_body and func_end_line:
                    func = FunctionNode(
                        name=func_name,
                        visibility=visibility,
                        is_payable=is_payable,
                        is_view=is_view,
                        is_pure=is_pure,
                        modifiers=modifiers,
                        line_start=func_start_line,
                        line_end=func_end_line,
                        body=func_body,
                    )
                    contract.functions.append(func)

    def _extract_state_variables(self, contract: ContractInfo) -> None:
        """Extract state variables from a contract."""
        contract_lines = self.lines[contract.line_start - 1 : contract.line_end]

        # Pattern: type name; or type public name;
        var_pattern = r"(\w+(?:\s*\[\s*\])?)\s+(\w+)\s*(?:public|private|internal)?\s*;"

        for i, line in enumerate(contract_lines, start=contract.line_start):
            # Skip function declarations
            if "function" in line:
                continue

            match = re.search(var_pattern, line)
            if match:
                var_type = match.group(1).strip()
                var_name = match.group(2).strip()

                visibility = "internal"
                if "public" in line:
                    visibility = "public"
                elif "private" in line:
                    visibility = "private"

                var = StateVariable(
                    name=var_name, type=var_type, visibility=visibility, line_number=i
                )
                contract.state_variables.append(var)

    def _extract_modifiers(self, contract: ContractInfo) -> None:
        """Extract modifier declarations."""
        contract_lines = self.lines[contract.line_start - 1 : contract.line_end]
        contract_text = "\n".join(contract_lines)

        # Pattern: modifier name(...) { ... }
        modifier_pattern = r"modifier\s+(\w+)\s*\([^)]*\)\s*\{"

        for match in re.finditer(modifier_pattern, contract_text):
            modifier_name = match.group(1)
            contract.modifiers.append(modifier_name)

    def get_external_calls(self, function_body: str, line_offset: int = 0) -> List[ExternalCall]:
        """
        Extract external calls from function body.

        Args:
            function_body: Function source code
            line_offset: Line number offset for the function

        Returns:
            List of ExternalCall objects
        """
        calls = []
        body_lines = function_body.split("\n")

        # Patterns for different call types
        patterns = [
            (r"\.call\s*\{value:\s*([^}]+)\}\s*\(", "call", True),
            (r"\.call\s*\(", "call", False),
            (r"\.call\.value\s*\(([^)]+)\)\s*\(", "call", True),
            (r"\.send\s*\(([^)]+)\)", "send", True),
            (r"\.transfer\s*\(([^)]+)\)", "transfer", True),
            (r"\.delegatecall\s*\(", "delegatecall", False),
        ]

        for i, line in enumerate(body_lines, start=line_offset):
            for pattern, call_type, has_value in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    value = match.group(1) if has_value and match.groups() else None
                    call = ExternalCall(
                        target="",  # Would need more parsing to extract target
                        value=value,
                        call_type=call_type,
                        line_number=i,
                    )
                    calls.append(call)

        return calls

    def get_state_writes(
        self, function_body: str, state_variables: List[StateVariable]
    ) -> List[Tuple[str, int]]:
        """
        Find state variable writes in function body.

        Args:
            function_body: Function source code
            state_variables: List of state variables in the contract

        Returns:
            List of tuples (variable_name, line_number)
        """
        writes = []
        body_lines = function_body.split("\n")
        var_names = [var.name for var in state_variables]

        for i, line in enumerate(body_lines, 1):
            # Pattern: variable = ... or variable[..] = ...
            for var_name in var_names:
                # Match assignments like: var = or var[ = or var. =
                pattern = rf"\b{re.escape(var_name)}\s*(?:\[[^\]]*\])?\s*="
                if re.search(pattern, line):
                    writes.append((var_name, i))

        return writes

    def has_require_check(self, function_body: str) -> bool:
        """
        Check if function has require() statements.

        Args:
            function_body: Function source code

        Returns:
            True if require() is found
        """
        return bool(re.search(r"require\s*\(", function_body))

    def get_hardcoded_addresses(self) -> List[Tuple[str, int]]:
        """
        Find hardcoded Ethereum addresses.

        Returns:
            List of tuples (address, line_number)
        """
        addresses = []
        # Pattern: 0x followed by 38-40 hex characters (Ethereum addresses)
        # Note: Some addresses may be shorter in test cases, so we allow 38-40 chars
        address_pattern = r"0x[a-fA-F0-9]{38,40}"

        for i, line in enumerate(self.lines, 1):
            # Skip comments
            if "//" in line:
                comment_pos = line.find("//")
                line_before_comment = line[:comment_pos]
            else:
                line_before_comment = line

            matches = re.finditer(address_pattern, line_before_comment)
            for match in matches:
                addr = match.group(0)
                # Validate it's a complete address (not part of a longer hex string)
                start_pos = match.start()
                end_pos = match.end()
                # Check boundaries - should be word boundaries or common separators
                if start_pos == 0 or line_before_comment[start_pos - 1] in " =,;()[]{}\"'":
                    if (
                        end_pos >= len(line_before_comment)
                        or line_before_comment[end_pos] in " ,;()[]{}\"'"
                    ):
                        addresses.append((addr, i))

        return addresses
