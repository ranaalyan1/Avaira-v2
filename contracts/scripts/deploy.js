const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying from:", deployer.address);
  console.log(
    "Balance:",
    ethers.formatEther(await deployer.provider.getBalance(deployer.address)),
    "AVAX"
  );

  const Registry = await ethers.getContractFactory("AgentRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  console.log("AgentRegistry:", await registry.getAddress());

  const Treasury = await ethers.getContractFactory("Treasury");
  const treasury = await Treasury.deploy();
  await treasury.waitForDeployment();
  console.log("Treasury:", await treasury.getAddress());

  const ExecWallet = await ethers.getContractFactory("ExecutionWallet");
  const execWallet = await ExecWallet.deploy(
    await registry.getAddress(),
    await treasury.getAddress(),
    deployer.address
  );
  await execWallet.waitForDeployment();
  console.log("ExecutionWallet:", await execWallet.getAddress());

  const FreezeSlash = await ethers.getContractFactory("FreezeSlash");
  const freezeSlash = await FreezeSlash.deploy(await registry.getAddress());
  await freezeSlash.waitForDeployment();
  console.log("FreezeSlash:", await freezeSlash.getAddress());

  const Reputation = await ethers.getContractFactory("ReputationEngine");
  const reputation = await Reputation.deploy();
  await reputation.waitForDeployment();
  console.log("ReputationEngine:", await reputation.getAddress());

  await registry.setProtocol(await execWallet.getAddress());
  await treasury.setExecutionWallet(await execWallet.getAddress());
  console.log("Permissions wired.");

  console.log("\n--- Copy to backend/.env ---");
  console.log(`AGENT_REGISTRY_ADDRESS=${await registry.getAddress()}`);
  console.log(`EXECUTION_WALLET_ADDRESS=${await execWallet.getAddress()}`);
  console.log(`FREEZE_SLASH_ADDRESS=${await freezeSlash.getAddress()}`);
  console.log(`TREASURY_ADDRESS=${await treasury.getAddress()}`);
  console.log(`REPUTATION_ENGINE_ADDRESS=${await reputation.getAddress()}`);
}

main().catch(console.error);
