// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract ReputationEngine is Ownable {
    uint256 public constant SUCCESS_BONUS = 2;
    uint256 public constant FAILURE_PENALTY = 5;
    uint256 public constant FREEZE_PENALTY = 20;
    uint256 public constant MAX_SCORE = 200;
    uint256 public constant INITIAL_SCORE = 100;

    mapping(bytes32 => uint256) public scores;

    event ScoreUpdated(bytes32 indexed agentId, uint256 oldScore, uint256 newScore, string reason);

    constructor() Ownable(msg.sender) {}

    function initScore(bytes32 agentId) external onlyOwner {
        if (scores[agentId] == 0) {
            scores[agentId] = INITIAL_SCORE;
        }
    }

    function onSuccess(bytes32 agentId) external onlyOwner {
        uint256 oldScore = scores[agentId];
        scores[agentId] = min(oldScore + SUCCESS_BONUS, MAX_SCORE);
        emit ScoreUpdated(agentId, oldScore, scores[agentId], "execution_success");
    }

    function onFailure(bytes32 agentId) external onlyOwner {
        uint256 oldScore = scores[agentId];
        scores[agentId] = oldScore > FAILURE_PENALTY ? oldScore - FAILURE_PENALTY : 0;
        emit ScoreUpdated(agentId, oldScore, scores[agentId], "execution_failure");
    }

    function onFreeze(bytes32 agentId) external onlyOwner {
        uint256 oldScore = scores[agentId];
        scores[agentId] = oldScore > FREEZE_PENALTY ? oldScore - FREEZE_PENALTY : 0;
        emit ScoreUpdated(agentId, oldScore, scores[agentId], "agent_frozen");
    }

    function getScore(bytes32 agentId) external view returns (uint256) {
        return scores[agentId] == 0 ? INITIAL_SCORE : scores[agentId];
    }

    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
}
