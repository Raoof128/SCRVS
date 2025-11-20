"""Tests for Solidity parser."""

import unittest
from pathlib import Path
from solidity_scanner.parser import SolidityParser, ContractInfo, FunctionNode


class TestParser(unittest.TestCase):
    """Test cases for SolidityParser."""
    
    def test_parse_simple_contract(self):
        """Test parsing a simple contract."""
        source = """
        pragma solidity ^0.8.0;
        
        contract TestContract {
            uint256 public value;
            
            function setValue(uint256 _value) public {
                value = _value;
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts[0].name, "TestContract")
    
    def test_extract_functions(self):
        """Test function extraction."""
        source = """
        contract Test {
            function test() public payable {
                // body
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        self.assertEqual(len(contracts), 1)
        self.assertGreater(len(contracts[0].functions), 0)
        self.assertEqual(contracts[0].functions[0].name, "test")
        self.assertTrue(contracts[0].functions[0].is_payable)
    
    def test_extract_state_variables(self):
        """Test state variable extraction."""
        source = """
        contract Test {
            uint256 public balance;
            address private owner;
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        self.assertEqual(len(contracts), 1)
        self.assertGreaterEqual(len(contracts[0].state_variables), 1)
    
    def test_get_external_calls(self):
        """Test external call detection."""
        source = """
        contract Test {
            function test() public {
                msg.sender.call{value: 100}("");
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        if contracts and contracts[0].functions:
            func = contracts[0].functions[0]
            calls = parser.get_external_calls(func.body, func.line_start)
            self.assertGreater(len(calls), 0)
    
    def test_get_state_writes(self):
        """Test state write detection."""
        source = """
        contract Test {
            uint256 public balance;
            
            function setBalance(uint256 amount) public {
                balance = amount;
            }
        }
        """
        
        parser = SolidityParser(source)
        contracts = parser.parse()
        
        if contracts and contracts[0].functions:
            func = contracts[0].functions[0]
            writes = parser.get_state_writes(func.body, contracts[0].state_variables)
            self.assertGreater(len(writes), 0)
    
    def test_get_hardcoded_addresses(self):
        """Test hardcoded address detection."""
        source = """
        contract Test {
            address constant ADMIN = 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0;
        }
        """
        
        parser = SolidityParser(source)
        addresses = parser.get_hardcoded_addresses()
        
        self.assertGreater(len(addresses), 0)


if __name__ == '__main__':
    unittest.main()

