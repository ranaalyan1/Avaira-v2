// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Treasury is Ownable {
    uint256 public constant TRUST_POOL_BPS = 7500;
    uint256 public constant REVENUE_BPS = 2500;

    uint256 public trustPoolBalance;
    uint256 public protocolRevenueBalance;
    uint256 public totalFeesReceived;

    address public executionWallet;

    event FeeReceived(uint256 total, uint256 trustPool, uint256 revenue);
    event RevenueWithdrawn(address indexed to, uint256 amount);

    modifier onlyExecutionWallet() {
        require(msg.sender == executionWallet || msg.sender == owner(), "Not authorized");
        _;
    }

    constructor() Ownable(msg.sender) {}

    function setExecutionWallet(address _ew) external onlyOwner {
        executionWallet = _ew;
    }

    receive() external payable onlyExecutionWallet {
        uint256 tp = (msg.value * TRUST_POOL_BPS) / 10000;
        uint256 rev = msg.value - tp;

        trustPoolBalance += tp;
        protocolRevenueBalance += rev;
        totalFeesReceived += msg.value;

        emit FeeReceived(msg.value, tp, rev);
    }

    function withdrawRevenue(address payable to, uint256 amount) external onlyOwner {
        require(amount <= protocolRevenueBalance, "Insufficient balance");
        protocolRevenueBalance -= amount;
        to.transfer(amount);
        emit RevenueWithdrawn(to, amount);
    }

    function getStats() external view returns (uint256, uint256, uint256) {
        return (totalFeesReceived, trustPoolBalance, protocolRevenueBalance);
    }
}
