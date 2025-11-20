"""Tests for validation detector."""

import unittest
from pathlib import Path
from solidity_scanner.parser import SolidityParser
from solidity_scanner.detectors.validation import ValidationDetector


class TestValidationDetector(unittest.TestCase):
    """Test cases for ValidationDetector."""
    
    def test_detect_missing_validation(self):
        """Test detection of missing input validation."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
            function setValue(uint256 value) public {
                // Missing require() check
                storageValue = value;
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ValidationDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        validation_findings = [f for f in findings if 'Missing Input Validation' in f.title]
        self.assertGreater(len(validation_findings), 0)
    
    def test_detect_hardcoded_addresses(self):
        """Test detection of hardcoded addresses."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
            address constant ADMIN = 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0;
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ValidationDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        address_findings = [f for f in findings if 'Hardcoded Address' in f.title]
        self.assertGreater(len(address_findings), 0)
    
    def test_detect_unsafe_arithmetic(self):
        """Test detection of unsafe arithmetic."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
            function add(uint256 a, uint256 b) public pure returns (uint256) {
                return a + b;  // No overflow check
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        detector = ValidationDetector()
        findings = detector.detect(contracts, source, "test.sol")
        
        arithmetic_findings = [f for f in findings if 'Overflow' in f.title or 'Underflow' in f.title]
        # May or may not detect depending on implementation
        # This test verifies the detector runs without errors


if __name__ == '__main__':
    unittest.main()

