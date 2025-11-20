"""Tests for reporter module."""

import unittest
import json
import os
from pathlib import Path
from solidity_scanner.detectors.base import Finding
from solidity_scanner.reporter import Reporter


class TestReporter(unittest.TestCase):
    """Test cases for Reporter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.findings = [
            Finding(
                severity='CRITICAL',
                title='Test Critical Finding',
                description='This is a test critical finding',
                file_path='test.sol',
                line_number=10,
                function_name='testFunction',
                code_snippet='test code',
                recommendation='Fix this',
                reference='https://example.com'
            ),
            Finding(
                severity='HIGH',
                title='Test High Finding',
                description='This is a test high finding',
                file_path='test.sol',
                line_number=20,
            ),
        ]
        self.reporter = Reporter(self.findings, 'test.sol')
    
    def test_generate_json(self):
        """Test JSON report generation."""
        output_path = 'test_report.json'
        try:
            self.reporter.generate_json(output_path)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            self.assertEqual(report['file'], 'test.sol')
            self.assertEqual(report['total_findings'], 2)
            self.assertEqual(len(report['findings']), 2)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_generate_csv(self):
        """Test CSV report generation."""
        output_path = 'test_findings.csv'
        try:
            self.reporter.generate_csv(output_path)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('Severity', content)
                self.assertIn('CRITICAL', content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_generate_markdown(self):
        """Test Markdown report generation."""
        output_path = 'test_audit.md'
        try:
            self.reporter.generate_markdown(output_path)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('# Smart Contract Security Audit Report', content)
                self.assertIn('CRITICAL', content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_get_exit_code(self):
        """Test exit code calculation."""
        # Should return 1 for critical/high findings
        exit_code = self.reporter.get_exit_code()
        self.assertEqual(exit_code, 1)
        
        # Should return 0 when critical_only=True but no critical findings in filtered set
        low_findings = [
            Finding(
                severity='LOW',
                title='Low Finding',
                description='Low severity',
                file_path='test.sol',
                line_number=1,
            )
        ]
        low_reporter = Reporter(low_findings, 'test.sol')
        exit_code = low_reporter.get_exit_code(critical_only=True)
        self.assertEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()

