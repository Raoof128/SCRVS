// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * SAFE CONTRACT EXAMPLE
 * 
 * This contract demonstrates secure patterns:
 * - CEI pattern (Checks-Effects-Interactions)
 * - Reentrancy guards
 * - Input validation
 * - Access control
 * - Event emissions
 */

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SafeBank is ReentrancyGuard, Ownable {
    mapping(address => uint256) public balances;
    
    // Events for important state changes
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event Transfer(address indexed from, address indexed to, uint256 amount);
    
    constructor() Ownable() {}
    
    // SAFE: Follows CEI pattern and uses reentrancy guard
    function withdraw(uint256 amount) public nonReentrant {
        // Checks
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(amount > 0, "Amount must be greater than zero");
        
        // Effects - Update state BEFORE external call
        balances[msg.sender] -= amount;
        
        // Interactions - External call AFTER state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        emit Withdrawal(msg.sender, amount);
    }
    
    // SAFE: Input validation
    function deposit() public payable {
        require(msg.value > 0, "Must send some ether");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    // SAFE: Proper access control
    function setBalance(address user, uint256 amount) public onlyOwner {
        require(user != address(0), "Invalid address");
        balances[user] = amount;
    }
    
    // SAFE: Event emission
    function transfer(address to, uint256 amount) public {
        require(to != address(0), "Invalid recipient");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(amount > 0, "Amount must be greater than zero");
        
        balances[msg.sender] -= amount;
        balances[to] += amount;
        
        emit Transfer(msg.sender, to, amount);
    }
    
    // SAFE: Using msg.sender instead of tx.origin
    function adminFunction() public onlyOwner {
        // Uses onlyOwner modifier which checks msg.sender
        // This is safe from phishing attacks
    }
    
    // SAFE: Proper external call with error handling
    function sendEther(address recipient, uint256 amount) public onlyOwner {
        require(recipient != address(0), "Invalid recipient");
        require(address(this).balance >= amount, "Insufficient contract balance");
        
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Transfer failed");
    }
}

