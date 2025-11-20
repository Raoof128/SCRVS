// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;

/**
 * VULNERABLE CONTRACT - DO NOT USE IN PRODUCTION
 * 
 * This contract demonstrates multiple security vulnerabilities:
 * - Reentrancy vulnerability
 * - Missing input validation
 * - Hardcoded addresses
 * - Insecure randomness
 * - Unprotected admin functions
 */

contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public owner;
    address constant ADMIN = 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb;
    
    // Missing nonReentrant modifier
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    // CRITICAL: Reentrancy vulnerability - external call before state update
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // External call BEFORE state update - VIOLATES CEI pattern
        msg.sender.call{value: amount}("");
        
        // State update happens AFTER external call - VULNERABLE
        balances[msg.sender] -= amount;
    }
    
    // HIGH: Missing input validation
    function deposit() public payable {
        // No validation of msg.value
        balances[msg.sender] += msg.value;
    }
    
    // HIGH: Insecure randomness
    function randomWinner() public view returns (address) {
        // Predictable randomness - can be manipulated by miners
        uint256 random = uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty)));
        // ... logic to select winner
    }
    
    // CRITICAL: Unprotected admin function
    function setOwner(address newOwner) public {
        // Missing onlyOwner modifier or require check
        owner = newOwner;
    }
    
    // MEDIUM: Deprecated call pattern
    function sendFunds(address recipient, uint256 amount) public {
        // Using deprecated transfer() - has gas limit
        recipient.transfer(amount);
    }
    
    // HIGH: Use of tx.origin
    function adminOnly() public {
        require(tx.origin == owner, "Not authorized");
        // Vulnerable to phishing attacks
    }
    
    // MEDIUM: Missing event emission
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        balances[to] += amount;
        // Missing Transfer event
    }
    
    // HIGH: Unsafe delegatecall
    function delegateCall(address target, bytes memory data) public {
        // Dangerous delegatecall without validation
        target.delegatecall(data);
    }
    
    // MEDIUM: Unchecked return value
    function sendEther(address recipient) public {
        // Not checking return value
        recipient.send(100);
    }
    
    receive() external payable {
        // Fallback can receive ether and modify state
        balances[msg.sender] += msg.value;
    }
}

