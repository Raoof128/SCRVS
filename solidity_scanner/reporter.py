"""
Report generation engine.

Generates reports in multiple formats:
- Terminal (colored output)
- JSON
- CSV
- Markdown (professional audit report)
"""

import csv
import json
import logging
from datetime import datetime
from typing import Dict, List

from .detectors.base import Finding
from .utils import get_severity_color

logger = logging.getLogger(__name__)


class Reporter:
    """Generates vulnerability reports in multiple formats."""

    def __init__(self, findings: List[Finding], file_path: str):
        """
        Initialize reporter.

        Args:
            findings: List of Finding objects
            file_path: Path to the scanned file
        """
        self.findings = findings
        self.file_path = file_path
        self.severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

    def print_terminal(self, critical_only: bool = False) -> None:
        """
        Print findings to terminal with color coding.

        Args:
            critical_only: If True, only show CRITICAL and HIGH findings
        """
        filtered_findings = self._filter_findings(critical_only)

        if not filtered_findings:
            print("\033[92m✓ No vulnerabilities found!\033[0m")
            return

        print(f"\n\033[1mScanning: {self.file_path}\033[0m")
        print("=" * 80)

        # Group by severity
        by_severity: Dict[str, List[Finding]] = {}
        for finding in filtered_findings:
            severity = finding.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(finding)

        # Print by severity order
        for severity in self.severity_order:
            if severity in by_severity:
                color_severity = get_severity_color(severity)
                print(f"\n{color_severity}")
                print("-" * 80)

                for finding in by_severity[severity]:
                    print(f"\n[{severity}] {finding.title}")
                    print(f"  File: {finding.file_path}:{finding.line_number}")
                    if finding.function_name:
                        print(f"  Function: {finding.function_name}")
                    print(f"  Description: {finding.description}")
                    if finding.code_snippet:
                        print(f"\n  Code:\n{finding.code_snippet}")
                    if finding.recommendation:
                        print(f"\n  Recommendation:\n  {finding.recommendation}")

        print("\n" + "=" * 80)
        print("\n\033[1mSummary:\033[0m")
        self._print_summary(filtered_findings)

    def _filter_findings(self, critical_only: bool) -> List[Finding]:
        """Filter findings based on severity."""
        if critical_only:
            return [f for f in self.findings if f.severity in ["CRITICAL", "HIGH"]]
        return self.findings

    def _print_summary(self, findings: List[Finding]) -> None:
        """Print summary statistics."""
        counts = {}
        for severity in self.severity_order:
            counts[severity] = sum(1 for f in findings if f.severity == severity)
            if counts[severity] > 0:
                color_severity = get_severity_color(severity)
                print(f"  {color_severity}: {counts[severity]}")

        total = len(findings)
        print(f"\n  Total findings: {total}")

    def generate_json(self, output_path: str) -> None:
        """
        Generate JSON report.

        Args:
            output_path: Path to output JSON file
        """
        report = {
            "file": self.file_path,
            "scan_date": datetime.now().isoformat(),
            "total_findings": len(self.findings),
            "findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "function_name": f.function_name,
                    "code_snippet": f.code_snippet,
                    "recommendation": f.recommendation,
                    "reference": f.reference,
                }
                for f in self.findings
            ],
            "summary": {
                severity: sum(1 for f in self.findings if f.severity == severity)
                for severity in self.severity_order
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"JSON report saved to {output_path}")

    def generate_csv(self, output_path: str) -> None:
        """
        Generate CSV report.

        Args:
            output_path: Path to output CSV file
        """
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Severity", "Title", "File", "Line", "Function", "Description", "Recommendation"]
            )

            for finding in self.findings:
                writer.writerow(
                    [
                        finding.severity,
                        finding.title,
                        finding.file_path,
                        finding.line_number,
                        finding.function_name,
                        finding.description.replace("\n", " "),
                        finding.recommendation.replace("\n", " "),
                    ]
                )

        logger.info(f"CSV report saved to {output_path}")

    def generate_markdown(self, output_path: str) -> None:
        """
        Generate professional Markdown audit report.

        Args:
            output_path: Path to output Markdown file
        """
        lines = []

        # Header
        lines.append("# Smart Contract Security Audit Report")
        lines.append("")
        lines.append(f"**File:** `{self.file_path}`")
        lines.append(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")

        summary = {
            severity: sum(1 for f in self.findings if f.severity == severity)
            for severity in self.severity_order
        }

        total = len(self.findings)
        critical_count = summary.get("CRITICAL", 0)
        high_count = summary.get("HIGH", 0)

        lines.append(
            f"This audit identified **{total}** security findings "
            f"across the analyzed smart contract."
        )
        lines.append("")
        lines.append("### Severity Breakdown")
        lines.append("")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for severity in self.severity_order:
            count = summary.get(severity, 0)
            if count > 0:
                lines.append(f"| {severity} | {count} |")
        lines.append("")

        if critical_count > 0 or high_count > 0:
            lines.append(
                f"⚠️ **{critical_count + high_count} critical/high severity issues** "
                f"require immediate attention."
            )
            lines.append("")

        # Findings by Severity
        for severity in self.severity_order:
            severity_findings = [f for f in self.findings if f.severity == severity]
            if not severity_findings:
                continue

            lines.append(f"## {severity} Findings")
            lines.append("")

            for i, finding in enumerate(severity_findings, 1):
                lines.append(f"### {i}. {finding.title}")
                lines.append("")
                lines.append(f"**Location:** `{finding.file_path}:{finding.line_number}`")
                if finding.function_name:
                    lines.append(f"**Function:** `{finding.function_name}`")
                lines.append("")
                lines.append("**Description:**")
                lines.append("")
                lines.append(finding.description)
                lines.append("")

                if finding.code_snippet:
                    lines.append("**Code Snippet:**")
                    lines.append("")
                    lines.append("```solidity")
                    lines.append(finding.code_snippet)
                    lines.append("```")
                    lines.append("")

                if finding.recommendation:
                    lines.append("**Recommendation:**")
                    lines.append("")
                    lines.append(finding.recommendation)
                    lines.append("")

                if finding.reference:
                    lines.append("**References:**")
                    lines.append("")
                    lines.append(finding.reference)
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Real-World Examples Section
        lines.append("## Real-World Reentrancy Attacks")
        lines.append("")
        lines.append("### The DAO Hack (2016)")
        lines.append("")
        lines.append(
            "The most famous reentrancy attack occurred in The DAO, where an attacker exploited"
        )
        lines.append(
            "a reentrancy vulnerability to drain approximately $60 million worth of Ether."
        )
        lines.append("The attack led to a hard fork of Ethereum.")
        lines.append("")
        lines.append("### Lendf.me (2020)")
        lines.append("")
        lines.append("A DeFi lending protocol lost $25 million due to a reentrancy vulnerability")
        lines.append("in its `deposit()` function. The attacker was able to re-enter the function")
        lines.append("before state updates were completed.")
        lines.append("")
        lines.append("### dForce (2020)")
        lines.append("")
        lines.append("Another DeFi protocol suffered a $25 million loss from a reentrancy attack.")
        lines.append("The vulnerability was in the token transfer mechanism.")
        lines.append("")
        lines.append("### Parity Wallet (2017)")
        lines.append("")
        lines.append("While not strictly a reentrancy attack, Parity Wallet's vulnerability")
        lines.append("involved unprotected functions and delegatecall misuse, resulting in")
        lines.append("$30 million being frozen.")
        lines.append("")

        # Recommendations Section
        lines.append("## General Recommendations")
        lines.append("")
        lines.append(
            "1. **Follow CEI Pattern**: Always update state (Effects) "
            "before making external calls (Interactions)"
        )
        lines.append(
            "2. **Use Reentrancy Guards**: Implement and use `nonReentrant` "
            "modifiers from OpenZeppelin"
        )
        lines.append("3. **Input Validation**: Validate all inputs with `require()` statements")
        lines.append("4. **Access Control**: Protect admin functions with proper modifiers")
        lines.append(
            "5. **Upgrade Solidity**: Use Solidity >= 0.8.0 for built-in overflow protection"
        )
        lines.append("6. **Code Review**: Always have smart contracts audited by security experts")
        lines.append("7. **Testing**: Write comprehensive tests, including edge cases")
        lines.append("8. **Events**: Emit events for important state changes")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*This report was generated by Solidity Vulnerability Scanner*")
        lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Markdown report saved to {output_path}")

    def get_exit_code(self, critical_only: bool = False) -> int:
        """
        Get exit code based on findings severity.

        Args:
            critical_only: If True, only consider CRITICAL and HIGH findings

        Returns:
            1 if HIGH/CRITICAL findings exist, 0 otherwise
        """
        if critical_only:
            critical_findings = [f for f in self.findings if f.severity in ["CRITICAL", "HIGH"]]
            return 1 if critical_findings else 0

        high_severity = [f for f in self.findings if f.severity in ["CRITICAL", "HIGH"]]
        return 1 if high_severity else 0
