// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract AgentRegistry is Ownable {
    enum AgentStatus {
        Active,
        Paused,
        Frozen
    }

    struct RiskEnvelope {
        uint256 maxTxValue;
        uint256 maxDailyTxns;
        uint256 maxSlippage;
    }

    struct Agent {
        bytes32 agentId;
        string name;
        address walletAddress;
        uint256 collateral;
        uint256 collateralRemaining;
        AgentStatus status;
        uint256 reputation;
        uint256 totalExecutions;
        uint256 successfulExecutions;
        RiskEnvelope riskEnvelope;
        uint256 registeredAt;
    }

    uint256 public constant MIN_COLLATERAL = 0.1 ether;

    mapping(bytes32 => Agent) public agents;
    mapping(address => bytes32[]) public agentsByWallet;
    bytes32[] public allAgentIds;
    address public protocol;

    event AgentRegistered(bytes32 indexed agentId, address indexed wallet, uint256 collateral);
    event AgentStatusUpdated(bytes32 indexed agentId, AgentStatus oldStatus, AgentStatus newStatus);
    event CollateralSlashed(bytes32 indexed agentId, uint256 amount);
    event ReputationUpdated(bytes32 indexed agentId, uint256 oldScore, uint256 newScore);

    modifier onlyProtocol() {
        require(msg.sender == protocol || msg.sender == owner(), "Not authorized");
        _;
    }

    constructor() Ownable(msg.sender) {}

    function setProtocol(address _protocol) external onlyOwner {
        protocol = _protocol;
    }

    function registerAgent(
        string calldata name,
        address walletAddress,
        RiskEnvelope calldata envelope
    ) external payable returns (bytes32 agentId) {
        require(msg.value >= MIN_COLLATERAL, "Insufficient collateral");

        agentId = keccak256(abi.encodePacked(walletAddress, name, block.timestamp));

        agents[agentId] = Agent({
            agentId: agentId,
            name: name,
            walletAddress: walletAddress,
            collateral: msg.value,
            collateralRemaining: msg.value,
            status: AgentStatus.Active,
            reputation: 100,
            totalExecutions: 0,
            successfulExecutions: 0,
            riskEnvelope: envelope,
            registeredAt: block.timestamp
        });

        agentsByWallet[walletAddress].push(agentId);
        allAgentIds.push(agentId);

        emit AgentRegistered(agentId, walletAddress, msg.value);
    }

    function updateStatus(bytes32 agentId, AgentStatus newStatus) external onlyProtocol {
        AgentStatus oldStatus = agents[agentId].status;
        agents[agentId].status = newStatus;
        emit AgentStatusUpdated(agentId, oldStatus, newStatus);
    }

    function slashCollateral(bytes32 agentId, uint256 amount) external onlyProtocol returns (uint256 slashed) {
        Agent storage a = agents[agentId];
        slashed = amount > a.collateralRemaining ? a.collateralRemaining : amount;
        a.collateralRemaining -= slashed;
        emit CollateralSlashed(agentId, slashed);
    }

    function updateReputation(bytes32 agentId, uint256 newScore) external onlyProtocol {
        uint256 oldScore = agents[agentId].reputation;
        agents[agentId].reputation = newScore;
        emit ReputationUpdated(agentId, oldScore, newScore);
    }

    function recordExecution(bytes32 agentId, bool success) external onlyProtocol {
        agents[agentId].totalExecutions++;
        if (success) {
            agents[agentId].successfulExecutions++;
        }
    }

    function isActive(bytes32 agentId) external view returns (bool) {
        return agents[agentId].status == AgentStatus.Active;
    }

    function getAgent(bytes32 agentId) external view returns (Agent memory) {
        return agents[agentId];
    }
}
