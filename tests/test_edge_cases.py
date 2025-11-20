"""Edge case tests for Solidity Vulnerability Scanner."""

import unittest
from pathlib import Path

from solidity_scanner.detectors import (
    BadPatternsDetector,
    ReentrancyDetector,
    ValidationDetector,
)
from solidity_scanner.parser import SolidityParser
from solidity_scanner.reporter import Reporter
from solidity_scanner.utils import find_solidity_files, read_file_content


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_contract(self):
        """Test parsing empty contract."""
        source = """
        pragma solidity ^0.8.0;
        
        contract Empty {
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        self.assertEqual(len(contracts), 1)
        self.assertEqual(len(contracts[0].functions), 0)

    def test_contract_with_only_state_variables(self):
        """Test contract with only state variables."""
        source = """
        pragma solidity ^0.8.0;
        
        contract Storage {
            uint256 public value;
            address public owner;
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        self.assertEqual(len(contracts), 1)
        self.assertEqual(len(contracts[0].state_variables), 2)

    def test_multiple_contracts(self):
        """Test file with multiple contracts."""
        source = """
        pragma solidity ^0.8.0;
        
        contract A {
            function test() public {}
        }
        
        contract B {
            function test() public {}
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        self.assertEqual(len(contracts), 2)

    def test_nested_braces(self):
        """Test contract with nested braces."""
        source = """
        pragma solidity ^0.8.0;
        
        contract Test {
            function test() public {
                if (true) {
                    if (false) {
                        value = 1;
                    }
                }
            }
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        self.assertEqual(len(contracts), 1)
        self.assertGreater(len(contracts[0].functions), 0)

    def test_comments_in_code(self):
        """Test code with various comment styles."""
        source = """
        pragma solidity ^0.8.0;
        
        contract Test {
            // Single line comment
            function test() public {
                /* Multi-line
                   comment */
                value = 1; // Inline comment
            }
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        self.assertEqual(len(contracts), 1)

    def test_missing_pragma(self):
        """Test contract without pragma statement."""
        source = """
        contract Test {
            function test() public {}
        }
        """

        parser = SolidityParser(source)
        contracts = parser.parse()

        # Should still parse successfully
        self.assertEqual(len(contracts), 1)

    def test_invalid_syntax_graceful_handling(self):
        """Test that invalid syntax doesn't crash the parser."""
        source = """
        contract Test {
            function test() public {
                // Missing closing brace intentionally
        """

        parser = SolidityParser(source)
        # Should not raise exception, may return empty or partial results
        try:
            contracts = parser.parse()
            # Parser should handle gracefully
            self.assertIsInstance(contracts, list)
        except Exception as e:
            self.fail(f"Parser should handle invalid syntax gracefully, but raised: {e}")

    def test_empty_findings_report(self):
        """Test reporter with empty findings list."""
        from solidity_scanner.detectors.base import Finding

        findings = []
        reporter = Reporter(findings, "test.sol")

        # Should not raise exception
        reporter.print_terminal()
        exit_code = reporter.get_exit_code()
        self.assertEqual(exit_code, 0)

    def test_file_not_found_handling(self):
        """Test handling of non-existent file."""
        from solidity_scanner.utils import read_file_content

        non_existent = Path("non_existent_file.sol")
        try:
            content = read_file_content(non_existent)
            # Should raise FileNotFoundError
            self.assertIsNone(content)
        except FileNotFoundError:
            # Expected behavior
            pass

    def test_find_solidity_files_empty_directory(self):
        """Test finding files in empty directory."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            files = find_solidity_files(tmpdir)
            self.assertEqual(len(files), 0)

    def test_detector_with_empty_contracts(self):
        """Test detectors with empty contract list."""
        detector = ReentrancyDetector()
        findings = detector.detect([], "", "test.sol")

        self.assertEqual(len(findings), 0)


if __name__ == "__main__":
    unittest.main()
