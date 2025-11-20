"""
Command-line interface for Solidity Vulnerability Scanner.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import logging

from .parser import SolidityParser
from .detectors import (
    ReentrancyDetector,
    ValidationDetector,
    BadPatternsDetector,
    InsecureCallsDetector,
)
from .reporter import Reporter
from .utils import find_solidity_files, read_file_content
from .logging_config import setup_logging, get_logger

# Initialize logging
setup_logging(level="INFO")
logger = get_logger(__name__)


def scan_file(file_path: Path, output_format: str = None, critical_only: bool = False) -> int:
    """
    Scan a single Solidity file.
    
    Args:
        file_path: Path to the Solidity file
        output_format: Output format (json, csv, markdown, or None for terminal)
        critical_only: Only show critical/high findings
        
    Returns:
        Exit code (0 for success, 1 for vulnerabilities found)
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file cannot be read or parsed
    """
    try:
        source_code = read_file_content(file_path)
        if not source_code:
            logger.error(f"Failed to read file: {file_path}")
            return 1
    except (FileNotFoundError, PermissionError, ValueError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        return 1
    
    # Parse contract
    parser = SolidityParser(source_code, file_path)
    contracts = parser.parse()
    
    if not contracts:
        logger.warning(f"No contracts found in {file_path}")
        return 0
    
    # Run detectors
    all_findings = []
    
    detectors = [
        ReentrancyDetector(),
        ValidationDetector(),
        BadPatternsDetector(),
        InsecureCallsDetector(),
    ]
    
    for detector in detectors:
        findings = detector.detect(contracts, source_code, str(file_path))
        all_findings.extend(findings)
    
    # Generate reports
    reporter = Reporter(all_findings, str(file_path))
    
    # Print terminal output
    if output_format is None:
        reporter.print_terminal(critical_only=critical_only)
    
    # Generate file outputs
    base_name = file_path.stem
    
    if output_format == 'json' or output_format is None:
        reporter.generate_json(f"{base_name}_report.json")
    
    if output_format == 'csv' or output_format is None:
        reporter.generate_csv(f"{base_name}_findings.csv")
    
    if output_format == 'markdown' or output_format is None:
        reporter.generate_markdown(f"{base_name}_security_audit.md")
    
    # Return exit code
    return reporter.get_exit_code(critical_only=critical_only)


def calculate_score(findings: List) -> float:
    """
    Calculate security score (0-100).
    
    Args:
        findings: List of Finding objects
        
    Returns:
        Security score as float
    """
    if not findings:
        return 100.0
    
    severity_weights = {
        'CRITICAL': 20,
        'HIGH': 15,
        'MEDIUM': 10,
        'LOW': 5,
        'INFO': 2,
    }
    
    total_penalty = sum(
        severity_weights.get(f.severity, 0)
        for f in findings
    )
    
    score = max(0, 100 - total_penalty)
    return score


def score_file(file_path: Path) -> int:
    """
    Calculate and display security score for a file.
    
    Args:
        file_path: Path to the Solidity file
        
    Returns:
        Exit code
    """
    source_code = read_file_content(file_path)
    if not source_code:
        logger.error(f"Failed to read file: {file_path}")
        return 1
    
    parser = SolidityParser(source_code, file_path)
    contracts = parser.parse()
    
    if not contracts:
        logger.warning(f"No contracts found in {file_path}")
        return 0
    
    # Run detectors
    all_findings = []
    
    detectors = [
        ReentrancyDetector(),
        ValidationDetector(),
        BadPatternsDetector(),
        InsecureCallsDetector(),
    ]
    
    for detector in detectors:
        findings = detector.detect(contracts, source_code, str(file_path))
        all_findings.extend(findings)
    
    score = calculate_score(all_findings)
    
    print(f"\nSecurity Score for {file_path}: {score:.1f}/100")
    print(f"Total Findings: {len(all_findings)}")
    
    if all_findings:
        severity_counts = {}
        for finding in all_findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        print("\nBreakdown:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                print(f"  {severity}: {count}")
    
    return 0


def main():
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for errors or vulnerabilities found)
    """
    parser = argparse.ArgumentParser(
        description='Solidity Vulnerability Scanner - Detect reentrancy and other security issues',
        epilog='For more information, see https://github.com/yourusername/solidity-scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-error output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan Solidity files for vulnerabilities')
    scan_parser.add_argument(
        'path',
        type=str,
        help='Path to Solidity file or directory'
    )
    scan_parser.add_argument(
        '--format',
        choices=['json', 'csv', 'markdown'],
        default=None,
        help='Output format (default: all formats)'
    )
    scan_parser.add_argument(
        '--critical-only',
        action='store_true',
        help='Only show CRITICAL and HIGH severity findings'
    )
    
    # Score command
    score_parser = subparsers.add_parser('score', help='Calculate security score')
    score_parser.add_argument(
        'path',
        type=str,
        help='Path to Solidity file'
    )
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="ERROR")
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'scan':
        sol_files = find_solidity_files(args.path)
        
        if not sol_files:
            logger.error(f"No Solidity files found in {args.path}")
            return 1
        
        exit_code = 0
        for sol_file in sol_files:
            logger.info(f"Scanning {sol_file}...")
            result = scan_file(sol_file, args.format, args.critical_only)
            if result != 0:
                exit_code = result
        
        return exit_code
    
    elif args.command == 'score':
        file_path = Path(args.path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 1
        
        return score_file(file_path)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

