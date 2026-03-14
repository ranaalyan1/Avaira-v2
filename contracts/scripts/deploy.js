const fs = require("fs");
const path = require("path");
const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying from:", deployer.address);
  console.log("Balance:", ethers.formatEther(await deployer.provider.getBalance(deployer.address)), "AVAX");

  const Registry = await ethers.getContractFactory("AgentRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();

  const Treasury = await ethers.getContractFactory("Treasury");
  const treasury = await Treasury.deploy();
  await treasury.waitForDeployment();

  const ExecutionWallet = await ethers.getContractFactory("ExecutionWallet");
  const executionWallet = await ExecutionWallet.deploy(await registry.getAddress(), await treasury.getAddress());
  await executionWallet.waitForDeployment();

  const FreezeSlash = await ethers.getContractFactory("FreezeSlash");
  const freezeSlash = await FreezeSlash.deploy(await registry.getAddress());
  await freezeSlash.waitForDeployment();

  const ReputationEngine = await ethers.getContractFactory("ReputationEngine");
  const reputationEngine = await ReputationEngine.deploy(await registry.getAddress());
  await reputationEngine.waitForDeployment();

  const InsurancePool = await ethers.getContractFactory("InsurancePool");
  const insurancePool = await InsurancePool.deploy();
  await insurancePool.waitForDeployment();

  await (await registry.setProtocol(await executionWallet.getAddress(), true)).wait();
  await (await registry.setProtocol(await freezeSlash.getAddress(), true)).wait();
  await (await registry.setProtocol(deployer.address, true)).wait();
  await (await treasury.setExecutionWallet(await executionWallet.getAddress())).wait();
  const trustPoolWallet = process.env.TRUST_POOL_WALLET || deployer.address;
  const protocolRevenueWallet = process.env.PROTOCOL_REVENUE_WALLET || deployer.address;
  const permitSigner = process.env.PERMIT_SIGNER || deployer.address;
  await (await treasury.setSplitWallets(trustPoolWallet, protocolRevenueWallet)).wait();
  await (await executionWallet.setPermitSigner(permitSigner)).wait();
  await (await freezeSlash.setProtocolAuthorized(deployer.address, true)).wait();
  await (await reputationEngine.setProtocolAuthorized(deployer.address, true)).wait();
  await (await insurancePool.setProtocolAuthorized(deployer.address, true)).wait();

  const deployedAddresses = {
    network: "fuji",
    chainId: 43113,
    deployer: deployer.address,
    AgentRegistry: await registry.getAddress(),
    Treasury: await treasury.getAddress(),
    ExecutionWallet: await executionWallet.getAddress(),
    FreezeSlash: await freezeSlash.getAddress(),
    ReputationEngine: await reputationEngine.getAddress(),
    InsurancePool: await insurancePool.getAddress(),
    trustPoolWallet,
    protocolRevenueWallet,
    permitSigner,
  };

  const outputPath = path.join(__dirname, "..", "deployedAddresses.json");
  const deploymentsDir = path.join(__dirname, "..", "..", "deployments");
  const fujiOutputPath = path.join(deploymentsDir, "fuji.json");
  fs.mkdirSync(deploymentsDir, { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(deployedAddresses, null, 2));
  fs.writeFileSync(fujiOutputPath, JSON.stringify(deployedAddresses, null, 2));

  console.log("AgentRegistry:", deployedAddresses.AgentRegistry);
  console.log("Treasury:", deployedAddresses.Treasury);
  console.log("ExecutionWallet:", deployedAddresses.ExecutionWallet);
  console.log("FreezeSlash:", deployedAddresses.FreezeSlash);
  console.log("ReputationEngine:", deployedAddresses.ReputationEngine);
  console.log("InsurancePool:", deployedAddresses.InsurancePool);
  console.log(`Saved deployed addresses to ${outputPath}`);
  console.log(`Saved Fuji deployment addresses to ${fujiOutputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
