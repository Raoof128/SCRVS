"""Tests for bad patterns detector."""

import unittest

from solidity_scanner.detectors.bad_patterns import BadPatternsDetector
from solidity_scanner.parser import SolidityParser


class TestBadPatternsDetector(unittest.TestCase):
    """Test cases for BadPatternsDetector."""

    def test_detect_insecure_randomness(self):
        """Test detection of insecure randomness."""
        source = """
        pragma solidity ^0.7.0;

        contract Test {
            function random() public view returns (uint256) {
                return uint256(keccak256(abi.encodePacked(block.timestamp)));
            }
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        detector = BadPatternsDetector()
        findings = detector.detect(contracts, source, "test.sol")

        randomness_findings = [f for f in findings if "Insecure Randomness" in f.title]
        self.assertGreater(len(randomness_findings), 0)

    def test_detect_tx_origin(self):
        """Test detection of tx.origin usage."""
        source = """
        pragma solidity ^0.7.0;

        contract Test {
            function admin() public {
                require(tx.origin == owner);
            }
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        detector = BadPatternsDetector()
        findings = detector.detect(contracts, source, "test.sol")

        tx_origin_findings = [f for f in findings if "tx.origin" in f.title]
        self.assertGreater(len(tx_origin_findings), 0)


if __name__ == "__main__":
    unittest.main()
