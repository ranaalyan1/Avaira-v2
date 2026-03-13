// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./AgentRegistry.sol";

contract FreezeSlash is Ownable {
    AgentRegistry public registry;

    struct SlashEvent {
        bytes32 agentId;
        uint256 amount;
        string reason;
        uint256 timestamp;
    }

    mapping(bytes32 => SlashEvent[]) public slashHistory;
    uint256 public constant DEFAULT_SLASH_RATE_BPS = 5000;

    event AgentFrozen(bytes32 indexed agentId, string reason, uint256 timestamp);
    event CollateralSlashed(bytes32 indexed agentId, uint256 amount, string reason);
    event AgentUnfrozen(bytes32 indexed agentId);

    constructor(address _registry) Ownable(msg.sender) {
        registry = AgentRegistry(_registry);
    }

    function freezeAgent(bytes32 agentId, string calldata reason) external onlyOwner {
        registry.updateStatus(agentId, AgentRegistry.AgentStatus.Frozen);
        emit AgentFrozen(agentId, reason, block.timestamp);
    }

    function slashCollateral(bytes32 agentId, uint256 amount, string calldata reason) external onlyOwner returns (uint256) {
        uint256 slashed = registry.slashCollateral(agentId, amount);
        slashHistory[agentId].push(SlashEvent(agentId, slashed, reason, block.timestamp));
        emit CollateralSlashed(agentId, slashed, reason);
        return slashed;
    }

    function unfreezeAgent(bytes32 agentId) external onlyOwner {
        registry.updateStatus(agentId, AgentRegistry.AgentStatus.Active);
        emit AgentUnfrozen(agentId);
    }
}
