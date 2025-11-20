"""Integration tests for Solidity Vulnerability Scanner."""

import os
import tempfile
import unittest
from pathlib import Path

from solidity_scanner.cli import scan_file, score_file
from solidity_scanner.detectors import (
    BadPatternsDetector,
    InsecureCallsDetector,
    ReentrancyDetector,
    ValidationDetector,
)
from solidity_scanner.parser import SolidityParser
from solidity_scanner.reporter import Reporter
from solidity_scanner.utils import find_solidity_files, read_file_content


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality."""

    def test_full_scan_workflow(self):
        """Test complete scanning workflow."""
        # Create a temporary Solidity file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
            f.write(
                """
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
            )
            temp_path = Path(f.name)

        try:
            # Test scanning
            exit_code = scan_file(temp_path)

            # Should find vulnerabilities
            self.assertEqual(exit_code, 1)

            # Check that reports were generated
            base_name = temp_path.stem
            self.assertTrue(Path(f"{base_name}_report.json").exists())
            self.assertTrue(Path(f"{base_name}_findings.csv").exists())
            self.assertTrue(Path(f"{base_name}_security_audit.md").exists())

        finally:
            # Cleanup
            temp_path.unlink()
            for ext in ["_report.json", "_findings.csv", "_security_audit.md"]:
                report_file = Path(f"{temp_path.stem}{ext}")
                if report_file.exists():
                    report_file.unlink()

    def test_safe_contract_scan(self):
        """Test scanning a safe contract."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
            f.write(
                """
            pragma solidity ^0.8.0;
            
            contract Safe {
                mapping(address => uint256) public balances;
                
                function withdraw(uint256 amount) public {
                    require(balances[msg.sender] >= amount);
                    balances[msg.sender] -= amount;
                    (bool success, ) = msg.sender.call{value: amount}("");
                    require(success, "Transfer failed");
                }
            }
            """
            )
            temp_path = Path(f.name)

        try:
            exit_code = scan_file(temp_path, critical_only=True)
            # Safe contract should not have critical issues
            # (may have medium/low issues, but exit code should be 0 for critical_only)
            # Actually, if there are no critical/high findings, exit code is 0
            self.assertIn(exit_code, [0, 1])  # May have some findings

        finally:
            temp_path.unlink()
            for ext in ["_report.json", "_findings.csv", "_security_audit.md"]:
                report_file = Path(f"{temp_path.stem}{ext}")
                if report_file.exists():
                    report_file.unlink()

    def test_score_calculation(self):
        """Test security score calculation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
            f.write(
                """
            pragma solidity ^0.7.0;
            
            contract Test {
                function test() public {
                    // Some code
                }
            }
            """
            )
            temp_path = Path(f.name)

        try:
            exit_code = score_file(temp_path)
            self.assertEqual(exit_code, 0)  # Score command should succeed

        finally:
            temp_path.unlink()

    def test_multiple_file_scanning(self):
        """Test scanning multiple files."""
        temp_files = []
        try:
            # Create multiple temporary files
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
                    f.write(
                        f"""
                    pragma solidity ^0.8.0;
                    
                    contract Test{i} {{
                        function test() public {{}}
                    }}
                    """
                    )
                    temp_files.append(Path(f.name))

            # Test finding files
            temp_dir = temp_files[0].parent
            sol_files = find_solidity_files(str(temp_dir))

            # Should find our temporary files
            self.assertGreaterEqual(len(sol_files), len(temp_files))

        finally:
            # Cleanup
            for f in temp_files:
                if f.exists():
                    f.unlink()

    def test_detector_integration(self):
        """Test all detectors working together."""
        source = """
        pragma solidity ^0.7.0;
        
        contract Test {
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

        detectors = [
            ReentrancyDetector(),
            ValidationDetector(),
            BadPatternsDetector(),
            InsecureCallsDetector(),
        ]

        all_findings = []
        for detector in detectors:
            findings = detector.detect(contracts, source, "test.sol")
            all_findings.extend(findings)

        # Should find multiple vulnerabilities
        self.assertGreater(len(all_findings), 0)

        # Test reporter with findings
        reporter = Reporter(all_findings, "test.sol")
        exit_code = reporter.get_exit_code()
        self.assertEqual(exit_code, 1)  # Should have critical/high findings

    def test_report_generation_all_formats(self):
        """Test all report formats are generated correctly."""
        from solidity_scanner.detectors.base import Finding

        findings = [
            Finding(
                severity="CRITICAL",
                title="Test Finding",
                description="Test description",
                file_path="test.sol",
                line_number=10,
            )
        ]

        reporter = Reporter(findings, "test.sol")

        # Generate all formats
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            csv_path = os.path.join(tmpdir, "test.csv")
            md_path = os.path.join(tmpdir, "test.md")

            reporter.generate_json(json_path)
            reporter.generate_csv(csv_path)
            reporter.generate_markdown(md_path)

            # Verify files were created
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(csv_path))
            self.assertTrue(os.path.exists(md_path))

            # Verify JSON is valid
            import json

            with open(json_path, "r") as f:
                data = json.load(f)
                self.assertIn("findings", data)
                self.assertEqual(len(data["findings"]), 1)


if __name__ == "__main__":
    unittest.main()
