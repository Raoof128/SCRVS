"""
Reentrancy vulnerability detector.

Detects patterns that could lead to reentrancy attacks:
- External calls before state updates (violation of CEI pattern)
- Missing nonReentrant modifier
- Deprecated call patterns
- Recursive fallback attack vectors
"""

import re
from typing import List
from .base import BaseDetector, Finding
from ..parser import ContractInfo, FunctionNode, ExternalCall


class ReentrancyDetector(BaseDetector):
    """Detects reentrancy vulnerabilities."""
    
    def detect(self, contracts: List[ContractInfo], source_code: str, file_path: str) -> List[Finding]:
        """
        Detect reentrancy vulnerabilities.
        
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
                # Skip view/pure functions
                if func.is_view or func.is_pure:
                    continue
                
                # Check for missing nonReentrant modifier
                self._check_missing_guard(func, contract, file_path)
                
                # Check CEI pattern violation
                self._check_cei_violation(func, contract, file_path, source_code)
                
                # Check for deprecated call patterns
                self._check_deprecated_calls(func, file_path)
                
                # Check for recursive fallback vectors
                self._check_fallback_vectors(func, contract, file_path)
        
        return self.findings
    
    def _check_missing_guard(
        self,
        func: FunctionNode,
        contract: ContractInfo,
        file_path: str
    ) -> None:
        """Check if function makes external calls without nonReentrant modifier."""
        # Check if function has external calls
        # Match patterns like: .call(...), .call{value:...}(...), .send(...), .transfer(...)
        has_external_call = bool(re.search(
            r'\.(call|send|transfer|delegatecall)(\s*\{[^}]*\})?\s*\(',
            func.body
        ))
        
        # Check if function is payable or modifies state
        has_state_change = bool(re.search(
            r'=\s*[^=]',
            func.body
        ))
        
        if has_external_call and 'nonReentrant' not in func.modifiers:
            # Check if contract has nonReentrant modifier available
            has_modifier = 'nonReentrant' in contract.modifiers
            
            if has_modifier:
                self.add_finding(
                    severity='HIGH',
                    title='Missing Reentrancy Guard',
                    description=(
                        f"Function '{func.name}' makes external calls but does not use "
                        f"the 'nonReentrant' modifier. This could allow reentrancy attacks."
                    ),
                    file_path=file_path,
                    line_number=func.line_start,
                    function_name=func.name,
                    recommendation=(
                        f"Add the 'nonReentrant' modifier to function '{func.name}':\n"
                        f"function {func.name}(...) nonReentrant {{ ... }}"
                    ),
                    reference="https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/"
                )
    
    def _check_cei_violation(
        self,
        func: FunctionNode,
        contract: ContractInfo,
        file_path: str,
        source_code: str
    ) -> None:
        """Check for Checks-Effects-Interactions pattern violations."""
        # Pattern for external calls
        call_patterns = [
            r'\.call\s*\{value:',
            r'\.call\s*\(',
            r'\.call\.value\s*\(',
            r'\.send\s*\(',
            r'\.transfer\s*\(',
        ]
        
        # Get state variable names
        state_var_names = [var.name for var in contract.state_variables]
        
        if not state_var_names:
            return
        
        # Find positions of external calls and state writes in function body
        func_body = func.body
        call_positions = []
        write_positions = []
        
        # Find external call positions
        for pattern in call_patterns:
            for match in re.finditer(pattern, func_body):
                call_positions.append(match.start())
        
        # Find state write positions (variable = ... or variable -= ... or variable += ...)
        for var_name in state_var_names:
            # Pattern: var = or var[ = or var -= or var += or var[ -= or var[ +=
            pattern = rf'\b{re.escape(var_name)}\s*(?:\[[^\]]*\])?\s*[-+]?='
            for match in re.finditer(pattern, func_body):
                write_positions.append((var_name, match.start()))
        
        if not call_positions or not write_positions:
            return
        
        # Check if any external call happens before a state write
        for call_pos in call_positions:
            for var_name, write_pos in write_positions:
                if call_pos < write_pos:
                    # Calculate line number
                    lines_before_call = func_body[:call_pos].count('\n')
                    call_line = func.line_start + lines_before_call
                    
                    # Found external call before state update - CRITICAL
                    self.add_finding(
                        severity='CRITICAL',
                        title='Reentrancy Vulnerability: External Call Before State Update',
                        description=(
                            f"Function '{func.name}' violates the Checks-Effects-Interactions (CEI) pattern. "
                            f"An external call occurs before state variable '{var_name}' is updated. "
                            f"This allows an attacker to re-enter the function and drain funds."
                        ),
                        file_path=file_path,
                        line_number=call_line,
                        function_name=func.name,
                        code_snippet=self._extract_code_snippet(source_code, call_line),
                        recommendation=(
                            "Follow the CEI pattern:\n"
                            "1. Checks: Validate all conditions\n"
                            "2. Effects: Update state variables\n"
                            "3. Interactions: Make external calls\n\n"
                            f"Move the state update for '{var_name}' before the external call."
                        ),
                        reference=(
                            "Real-world examples:\n"
                            "- The DAO Hack (2016): $60M stolen\n"
                            "- Lendf.me (2020): $25M stolen\n"
                            "- dForce (2020): $25M stolen\n"
                            "https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/"
                        )
                    )
                    break
    
    def _check_deprecated_calls(self, func: FunctionNode, file_path: str) -> None:
        """Check for deprecated call patterns."""
        deprecated_patterns = [
            (r'\.call\.value\s*\(', 'call.value()', 'HIGH'),
            (r'\.send\s*\(', 'send()', 'MEDIUM'),
            (r'\.transfer\s*\(', 'transfer()', 'MEDIUM'),
        ]
        
        for pattern, method_name, severity in deprecated_patterns:
            matches = re.finditer(pattern, func.body)
            for match in matches:
                # Calculate line number
                line_num = func.line_start + func.body[:match.start()].count('\n')
                
                self.add_finding(
                    severity=severity,
                    title=f'Deprecated Call Pattern: {method_name}',
                    description=(
                        f"Function '{func.name}' uses the deprecated {method_name} pattern. "
                        f"{method_name} has a gas limit of 2300 and can fail silently. "
                        f"Use low-level call() with proper error handling instead."
                    ),
                    file_path=file_path,
                    line_number=line_num,
                    function_name=func.name,
                    recommendation=(
                        f"Replace {method_name} with:\n"
                        "(bool success, ) = recipient.call{value: amount}(\"\");\n"
                        "require(success, \"Transfer failed\");"
                    ),
                    reference="https://consensys.github.io/smart-contract-best-practices/development-recommendations/solidity-specific/tx-origin/"
                )
    
    def _check_fallback_vectors(
        self,
        func: FunctionNode,
        contract: ContractInfo,
        file_path: str
    ) -> None:
        """Check for functions that could be called via fallback."""
        # Check if function is public/external and payable
        if func.visibility in ['public', 'external'] and func.is_payable:
            # Check if it modifies state
            has_state_change = bool(re.search(
                r'=\s*[^=]',
                func.body
            ))
            
            if has_state_change:
                # Check if it has proper access control
                has_access_control = bool(re.search(
                    r'require\s*\(.*msg\.sender',
                    func.body
                ))
                
                if not has_access_control:
                    self.add_finding(
                        severity='MEDIUM',
                        title='Potential Reentrancy via Fallback',
                        description=(
                            f"Function '{func.name}' is public/external and payable, "
                            f"making it callable via fallback functions. If it modifies state "
                            f"without proper guards, it could be exploited in a reentrancy attack."
                        ),
                        file_path=file_path,
                        line_number=func.line_start,
                        function_name=func.name,
                        recommendation=(
                            f"Add access control or reentrancy guard to '{func.name}':\n"
                            f"- Use 'nonReentrant' modifier\n"
                            f"- Add require() checks for authorized callers"
                        ),
                        reference="https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/"
                    )
    
    def _extract_code_snippet(self, source_code: str, line_number: int, context: int = 3) -> str:
        """Extract code snippet around a line number."""
        lines = source_code.split('\n')
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        
        snippet_lines = []
        for i in range(start, end):
            marker = '>>> ' if i == line_number - 1 else '    '
            snippet_lines.append(f"{marker}{i + 1:4d} | {lines[i]}")
        
        return '\n'.join(snippet_lines)

