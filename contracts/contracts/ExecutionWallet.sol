// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./AgentRegistry.sol";
import "./Treasury.sol";

contract ExecutionWallet is ReentrancyGuard, Ownable {
    AgentRegistry public registry;
    Treasury public treasury;

    uint256 public constant FEE_BPS = 50;

    bytes32 public DOMAIN_SEPARATOR;
    bytes32 public constant PERMIT_TYPEHASH = keccak256(
        "ExecutionPermit(bytes32 agentId,bytes32 executionId,bytes32 actionHash,uint256 value,uint256 nonce,uint256 deadline)"
    );

    mapping(bytes32 => uint256) public nonces;
    address public permittedSigner;

    event PermitVerified(bytes32 indexed executionId, bytes32 indexed agentId);
    event TransactionExecuted(bytes32 indexed executionId, bytes32 indexed agentId, uint256 value, uint256 fee);
    event FeeDeducted(bytes32 indexed executionId, uint256 fee, uint256 trustPool, uint256 revenue);

    struct ExecutionPermit {
        bytes32 agentId;
        bytes32 executionId;
        bytes32 actionHash;
        uint256 value;
        uint256 nonce;
        uint256 deadline;
    }

    constructor(address _registry, address payable _treasury, address _signer) Ownable(msg.sender) {
        registry = AgentRegistry(_registry);
        treasury = Treasury(_treasury);
        permittedSigner = _signer;
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256("AVAIRA_ExecutionWallet"),
                keccak256("1"),
                block.chainid,
                address(this)
            )
        );
    }

    function setSigner(address _signer) external onlyOwner {
        permittedSigner = _signer;
    }

    function verifyPermit(ExecutionPermit calldata permit, bytes calldata sig) public view returns (bool) {
        require(block.timestamp <= permit.deadline, "Permit expired");
        require(nonces[permit.agentId] + 1 == permit.nonce, "Invalid nonce");

        bytes32 structHash = keccak256(
            abi.encode(
                PERMIT_TYPEHASH,
                permit.agentId,
                permit.executionId,
                permit.actionHash,
                permit.value,
                permit.nonce,
                permit.deadline
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        address recovered = recoverSigner(digest, sig);

        return recovered == permittedSigner;
    }

    function executeApprovedTransaction(
        ExecutionPermit calldata permit,
        bytes calldata sig,
        address payable target
    ) external payable nonReentrant returns (bytes32) {
        require(registry.isActive(permit.agentId), "Agent not active");
        require(verifyPermit(permit, sig), "Invalid permit");

        nonces[permit.agentId]++;
        emit PermitVerified(permit.executionId, permit.agentId);

        uint256 fee = (permit.value * FEE_BPS) / 10000;
        uint256 netValue = permit.value - fee;

        (bool feeSent, ) = address(treasury).call{value: fee}("");
        require(feeSent, "Fee transfer failed");
        emit FeeDeducted(permit.executionId, fee, (fee * 7500) / 10000, (fee * 2500) / 10000);

        (bool sent, ) = target.call{value: netValue}("");
        require(sent, "Execution transfer failed");

        registry.recordExecution(permit.agentId, true);
        emit TransactionExecuted(permit.executionId, permit.agentId, permit.value, fee);

        return permit.executionId;
    }

    function recoverSigner(bytes32 digest, bytes memory sig) internal pure returns (address) {
        require(sig.length == 65, "Invalid sig length");
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
        if (v < 27) {
            v += 27;
        }
        return ecrecover(digest, v, r, s);
    }

    receive() external payable {}
}
