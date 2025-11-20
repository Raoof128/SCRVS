"""
Bad patterns detector.

Detects insecure randomness, unprotected admin functions, missing events, etc.
"""

import re
from typing import List
from .base import BaseDetector, Finding
from ..parser import ContractInfo, FunctionNode


class BadPatternsDetector(BaseDetector):
    """Detects bad patterns and anti-patterns."""
    
    def detect(self, contracts: List[ContractInfo], source_code: str, file_path: str) -> List[Finding]:
        """
        Detect bad patterns.
        
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
                # Check for insecure randomness
                self._check_insecure_randomness(func, file_path)
                
                # Check for unprotected admin functions
                self._check_unprotected_admin(func, file_path)
                
                # Check for missing events on state changes
                self._check_missing_events(func, contract, file_path)
        
        # Check for tx.origin usage
        self._check_tx_origin(source_code, file_path)
        
        return self.findings
    
    def _check_insecure_randomness(self, func: FunctionNode, file_path: str) -> None:
        """Check for insecure randomness sources."""
        insecure_patterns = [
            (r'block\.timestamp', 'block.timestamp'),
            (r'block\.number', 'block.number'),
            (r'blockhash\s*\(', 'blockhash()'),
            (r'block\.difficulty', 'block.difficulty'),
        ]
        
        for pattern, source_name in insecure_patterns:
            if re.search(pattern, func.body):
                line_num = func.line_start
                
                self.add_finding(
                    severity='HIGH',
                    title=f'Insecure Randomness: {source_name}',
                    description=(
                        f"Function '{func.name}' uses {source_name} for randomness. "
                        f"Block properties are predictable and can be manipulated by miners. "
                        f"This makes the contract vulnerable to exploitation."
                    ),
                    file_path=file_path,
                    line_number=line_num,
                    function_name=func.name,
                    recommendation=(
                        "Use a commit-reveal scheme or Chainlink VRF for secure randomness:\n"
                        "// Commit-reveal scheme\n"
                        "// Or use Chainlink VRF\n"
                        "import \"@chainlink/contracts/src/v0.8/VRFConsumerBase.sol\";"
                    ),
                    reference=(
                        "Real-world examples:\n"
                        "- Fomo3D: Predictable randomness exploited\n"
                        "https://consensys.github.io/smart-contract-best-practices/development-recommendations/solidity-specific/randomness/"
                    )
                )
    
    def _check_unprotected_admin(self, func: FunctionNode, file_path: str) -> None:
        """Check for unprotected admin functions."""
        admin_keywords = ['admin', 'owner', 'onlyOwner', 'setOwner', 'transferOwnership']
        
        is_admin_function = any(keyword.lower() in func.name.lower() for keyword in admin_keywords)
        
        if is_admin_function:
            # Check for access control modifiers
            has_access_control = any(
                modifier in ['onlyOwner', 'onlyAdmin', 'onlyRole'] 
                for modifier in func.modifiers
            )
            
            # Check for require() checks
            has_require = bool(re.search(
                r'require\s*\(.*msg\.sender',
                func.body
            ))
            
            if not has_access_control and not has_require:
                self.add_finding(
                    severity='CRITICAL',
                    title='Unprotected Admin Function',
                    description=(
                        f"Function '{func.name}' appears to be an admin function but lacks "
                        f"access control. Anyone can call this function, potentially allowing "
                        f"unauthorized changes to the contract."
                    ),
                    file_path=file_path,
                    line_number=func.line_start,
                    function_name=func.name,
                    recommendation=(
                        f"Add access control to '{func.name}':\n"
                        "modifier onlyOwner() {\n"
                        "    require(msg.sender == owner, \"Not owner\");\n"
                        "    _;\n"
                        "}\n\n"
                        f"function {func.name}(...) onlyOwner {{ ... }}"
                    ),
                    reference=(
                        "Real-world examples:\n"
                        "- Parity Wallet Hack: Unprotected init function\n"
                        "https://consensys.github.io/smart-contract-best-practices/development-recommendations/general/external-calls/"
                    )
                )
    
    def _check_missing_events(self, func: FunctionNode, contract: ContractInfo, file_path: str) -> None:
        """Check for missing events on important state changes."""
        # Check if function modifies state
        has_state_change = bool(re.search(
            r'=\s*[^=]',
            func.body
        ))
        
        if has_state_change:
            # Check for event emissions
            has_event = bool(re.search(
                r'emit\s+\w+\s*\(',
                func.body
            ))
            
            # Important functions should emit events
            important_keywords = ['transfer', 'withdraw', 'deposit', 'mint', 'burn', 'approve']
            is_important = any(keyword in func.name.lower() for keyword in important_keywords)
            
            if is_important and not has_event:
                self.add_finding(
                    severity='LOW',
                    title='Missing Event Emission',
                    description=(
                        f"Function '{func.name}' modifies state but does not emit an event. "
                        f"Events are important for off-chain monitoring and transparency."
                    ),
                    file_path=file_path,
                    line_number=func.line_start,
                    function_name=func.name,
                    recommendation=(
                        f"Add an event declaration and emit it in '{func.name}':\n"
                        "event Transfer(address indexed from, address indexed to, uint256 value);\n"
                        "emit Transfer(msg.sender, recipient, amount);"
                    ),
                    reference="https://consensys.github.io/smart-contract-best-practices/development-recommendations/general/events/"
                )
    
    def _check_tx_origin(self, source_code: str, file_path: str) -> None:
        """Check for tx.origin usage."""
        lines = source_code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if re.search(r'\btx\.origin\b', line):
                # Skip if it's in a comment
                if '//' in line[:line.find('tx.origin')] or '/*' in line[:line.find('tx.origin')]:
                    continue
                
                self.add_finding(
                    severity='HIGH',
                    title='Use of tx.origin',
                    description=(
                        "tx.origin is used for authorization. This is vulnerable to phishing attacks. "
                        "An attacker can trick a user into calling a malicious contract, which then "
                        "calls your contract. tx.origin will be the user's address, not the attacker's."
                    ),
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line.strip(),
                    recommendation=(
                        "Use msg.sender instead of tx.origin:\n"
                        "require(msg.sender == owner, \"Not authorized\");\n"
                        "// NOT: require(tx.origin == owner, \"Not authorized\");"
                    ),
                    reference=(
                        "Real-world examples:\n"
                        "- Multiple phishing attacks exploiting tx.origin\n"
                        "https://consensys.github.io/smart-contract-best-practices/development-recommendations/solidity-specific/tx-origin/"
                    )
                )

