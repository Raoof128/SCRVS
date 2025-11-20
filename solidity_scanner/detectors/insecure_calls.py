"""
Insecure calls detector.

Detects unsafe delegatecall usage and other insecure call patterns.
"""

import re
from typing import List
from .base import BaseDetector, Finding
from ..parser import ContractInfo, FunctionNode


class InsecureCallsDetector(BaseDetector):
    """Detects insecure call patterns."""
    
    def detect(self, contracts: List[ContractInfo], source_code: str, file_path: str) -> List[Finding]:
        """
        Detect insecure call patterns.
        
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
                # Check for delegatecall usage
                self._check_delegatecall(func, file_path)
                
                # Check for unchecked return values
                self._check_unchecked_returns(func, file_path)
        
        return self.findings
    
    def _check_delegatecall(self, func: FunctionNode, file_path: str) -> None:
        """Check for unsafe delegatecall usage."""
        if re.search(r'\.delegatecall\s*\(', func.body):
            # Check if target is user-controlled
            has_user_input = bool(re.search(
                r'msg\.data|msg\.sender|abi\.decode',
                func.body
            ))
            
            line_num = func.line_start
            
            if has_user_input:
                severity = 'CRITICAL'
                description = (
                    f"Function '{func.name}' uses delegatecall with user-controlled input. "
                    f"This is extremely dangerous as it allows an attacker to execute arbitrary code "
                    f"in the context of your contract, potentially taking full control."
                )
            else:
                severity = 'HIGH'
                description = (
                    f"Function '{func.name}' uses delegatecall. Delegatecall executes code in the "
                    f"context of the calling contract, which can lead to storage collisions and "
                    f"unexpected behavior if not handled carefully."
                )
            
            self.add_finding(
                severity=severity,
                title='Unsafe delegatecall Usage',
                description=description,
                file_path=file_path,
                line_number=line_num,
                function_name=func.name,
                recommendation=(
                    "Avoid delegatecall unless absolutely necessary. If you must use it:\n"
                    "1. Validate the target address\n"
                    "2. Use a whitelist of allowed contracts\n"
                    "3. Consider using a proxy pattern with proper access control"
                ),
                reference=(
                    "Real-world examples:\n"
                    "- Parity Wallet Hack (2017): $30M frozen due to delegatecall bug\n"
                    "- Multiple exploits involving delegatecall\n"
                    "https://consensys.github.io/smart-contract-best-practices/development-recommendations/solidity-specific/delegatecall/"
                )
            )
    
    def _check_unchecked_returns(self, func: FunctionNode, file_path: str) -> None:
        """Check for unchecked return values from external calls."""
        # Pattern: external call without checking return value
        call_patterns = [
            r'(\w+)\.(call|send|delegatecall)\s*\(',
        ]
        
        for pattern in call_patterns:
            matches = re.finditer(pattern, func.body)
            for match in matches:
                call_start = match.start()
                call_line = func.line_start + func.body[:call_start].count('\n')
                
                # Check if return value is captured
                call_snippet = func.body[call_start:call_start+200]
                
                # Look for (bool success, ) pattern
                has_return_check = bool(re.search(
                    r'\(bool\s+\w+',
                    call_snippet
                ))
                
                # Check if there's a require() after the call
                remaining_body = func.body[call_start:]
                has_require_after = bool(re.search(
                    r'require\s*\(',
                    remaining_body[:500]
                ))
                
                if not has_return_check and not has_require_after:
                    self.add_finding(
                        severity='MEDIUM',
                        title='Unchecked Return Value from External Call',
                        description=(
                            f"Function '{func.name}' makes an external call but does not check "
                            f"the return value. If the call fails, execution continues, which could "
                            f"lead to unexpected behavior."
                        ),
                        file_path=file_path,
                        line_number=call_line,
                        function_name=func.name,
                        recommendation=(
                            "Always check return values:\n"
                            "(bool success, bytes memory data) = target.call{value: amount}(\"\");\n"
                            "require(success, \"Call failed\");"
                        ),
                        reference="https://consensys.github.io/smart-contract-best-practices/development-recommendations/general/external-calls/"
                    )

