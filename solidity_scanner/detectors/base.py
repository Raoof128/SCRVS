"""
Base detector class for vulnerability detection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Finding:
    """Represents a security finding."""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    file_path: str
    line_number: int
    function_name: str = ""
    code_snippet: str = ""
    recommendation: str = ""
    reference: str = ""


class BaseDetector(ABC):
    """Base class for all vulnerability detectors."""

    def __init__(self):
        self.findings: List[Finding] = []

    @abstractmethod
    def detect(self, contracts: List[Any], source_code: str, file_path: str) -> List[Finding]:
        """
        Detect vulnerabilities in contracts.

        Args:
            contracts: List of ContractInfo objects
            source_code: Full source code
            file_path: Path to the source file

        Returns:
            List of Finding objects
        """
        pass

    def add_finding(
        self,
        severity: str,
        title: str,
        description: str,
        file_path: str,
        line_number: int,
        function_name: str = "",
        code_snippet: str = "",
        recommendation: str = "",
        reference: str = "",
    ) -> None:
        """Add a finding to the results."""
        finding = Finding(
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            code_snippet=code_snippet,
            recommendation=recommendation,
            reference=reference,
        )
        self.findings.append(finding)
