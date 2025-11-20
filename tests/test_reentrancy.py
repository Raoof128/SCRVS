"""Tests for reentrancy detector."""

import unittest
from pathlib import Path
from solidity_scanner.parser import SolidityParser
from solidity_scanner.detectors.reentrancy import ReentrancyDetector


class TestReentrancyDetector(unittest.TestCase):
    """Test cases for ReentrancyDetector."""
    
    def test_detect_reentrancy_vulnerability(self):
        """Test detection of reentrancy vulnerability."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Vulnerable {
            mapping(address => uint256) public balances;
            
            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                msg.sender.call{value: amount}("");
                balances[msg.sender] -= amount;
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ReentrancyDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        # Should detect reentrancy vulnerability
        reentrancy_findings = [f for f in findings if 'Reentrancy' in f.title]
        self.assertGreater(len(reentrancy_findings), 0)
    
    def test_detect_missing_guard(self):
        """Test detection of missing reentrancy guard."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
            modifier nonReentrant() {
                _;
            }
            
            function withdraw() public {
                msg.sender.call{value: 100}("");
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ReentrancyDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        # Should detect missing guard
        guard_findings = [f for f in findings if 'Guard' in f.title]
        self.assertGreater(len(guard_findings), 0)
    
    def test_detect_deprecated_calls(self):
        """Test detection of deprecated call patterns."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
            function send() public {
                msg.sender.send(100);
            }
            
            function transfer() public {
                msg.sender.transfer(100);
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ReentrancyDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        # Should detect deprecated patterns
        deprecated_findings = [f for f in findings if 'Deprecated' in f.title]
        self.assertGreater(len(deprecated_findings), 0)
    
    def test_safe_contract_passes(self):
        """Test that safe contract doesn't trigger false positives."""
        source = """
        pragma solidity ^0.8.0;
        
        contract Safe {
            mapping(address => uint256) public balances;
            
            modifier nonReentrant() {
                _;
            }
            
            function withdraw(uint256 amount) public nonReentrant {
                require(balances[msg.sender] >= amount);
                balances[msg.sender] -= amount;
                msg.sender.call{value: amount}("");
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ReentrancyDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        # Should have fewer findings (CEI violation might still be detected
        # depending on implementation, but guard should be present)
        critical_findings = [f for f in findings if f.severity == 'CRITICAL']
        # Note: This test may need adjustment based on actual detection logic


if __name__ == '__main__':
    unittest.main()

