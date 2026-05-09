/**
 * AVAIRA Protocol — Multi-Network Deployment
 * Deploys all 6 contracts in dependency order.
 * Saves addresses to /deployments/{network}.json.
 * Safe to re-run — skips already-deployed contracts.
 *
 * Order:
 *   1. AgentRegistry       (no deps)
 *   2. Treasury            (no deps)
 *   3. FreezeSlash         (AgentRegistry)
 *   4. ReputationEngine    (AgentRegistry)
 *   5. InsurancePool       (no deps)
 *   6. ExecutionWallet     (AgentRegistry + Treasury)
 */
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");
const { ethers } = hre;

async function main() {
  const [deployer] = await ethers.getSigners();
  const networkName = hre.network.name;
  const deployerBalance = await ethers.provider.getBalance(deployer.address);
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  const deploymentsFile = path.join(deploymentsDir, `${networkName}.json`);

  console.log(`\n🔺 AVAIRA Protocol Deployment`);
  console.log(`   Network:  ${networkName} (chain ${hre.network.config.chainId})`);
  console.log(`   Deployer: ${deployer.address}`);
  console.log(`   Balance:  ${ethers.formatEther(deployerBalance)} AVAX\n`);

  if (!fs.existsSync(deploymentsDir)) fs.mkdirSync(deploymentsDir, { recursive: true });

  const addresses = fs.existsSync(deploymentsFile)
    ? JSON.parse(fs.readFileSync(deploymentsFile, "utf8"))
    : {};

  async function deployIfNeeded(name, args = [], dependsOn = []) {
    if (addresses[name]) {
      console.log(`   ✓ ${name} already deployed at ${addresses[name]}`);
      return addresses[name];
    }
    for (const dep of dependsOn) {
      if (!addresses[dep]) throw new Error(`${name} depends on ${dep} — not deployed`);
    }
    console.log(`   ⟳ Deploying ${name}${args.length ? " with args" : ""}...`);
    const Factory = await ethers.getContractFactory(name);
    const contract = await Factory.deploy(...args);
    await contract.waitForDeployment();
    const addr = await contract.getAddress();
    addresses[name] = addr;
    fs.writeFileSync(deploymentsFile, JSON.stringify(addresses, null, 2));
    console.log(`   ✓ ${name} deployed at ${addr}`);
    return addr;
  }

  // ── Deploy in dependency order ────────────────────────────────
  const registryAddr    = await deployIfNeeded("AgentRegistry");
  const treasuryAddr    = await deployIfNeeded("Treasury");
  const freezeSlashAddr = await deployIfNeeded("FreezeSlash",      [registryAddr], ["AgentRegistry"]);
  const reputationAddr  = await deployIfNeeded("ReputationEngine", [registryAddr], ["AgentRegistry"]);
  const insuranceAddr   = await deployIfNeeded("InsurancePool");
  const walletAddr      = await deployIfNeeded("ExecutionWallet",  [registryAddr, treasuryAddr], ["AgentRegistry", "Treasury"]);

  // ── Wire cross-contract references ────────────────────────────
  console.log("\n   Wiring contracts...");
  const registry        = await ethers.getContractAt("AgentRegistry", registryAddr);
  const treasury        = await ethers.getContractAt("Treasury", treasuryAddr);
  const executionWallet = await ethers.getContractAt("ExecutionWallet", walletAddr);
  const freezeSlash     = await ethers.getContractAt("FreezeSlash", freezeSlashAddr);
  const reputation      = await ethers.getContractAt("ReputationEngine", reputationAddr);
  const insurance       = await ethers.getContractAt("InsurancePool", insuranceAddr);

  // Authorize protocol actors on registry
  const tx1 = await registry.setProtocol(walletAddr, true);
  await tx1.wait();
  const tx2 = await registry.setProtocol(freezeSlashAddr, true);
  await tx2.wait();
  const tx3 = await registry.setProtocol(deployer.address, true);
  await tx3.wait();

  // Treasury: set execution wallet + split wallets
  const tx4 = await treasury.setExecutionWallet(walletAddr);
  await tx4.wait();
  const trustWallet = process.env.TRUST_POOL_WALLET || deployer.address;
  const revWallet   = process.env.PROTOCOL_REVENUE_WALLET || deployer.address;
  const tx5 = await treasury.setSplitWallets(trustWallet, revWallet);
  await tx5.wait();

  // ExecutionWallet: set permit signer
  const permitSigner = process.env.PERMIT_SIGNER || deployer.address;
  const tx6 = await executionWallet.setPermitSigner(permitSigner);
  await tx6.wait();

  // FreezeSlash: authorize deployer
  const tx7 = await freezeSlash.setProtocolAuthorized(deployer.address, true);
  await tx7.wait();

  // Reputation: authorize deployer
  const tx8 = await reputation.setProtocolAuthorized(deployer.address, true);
  await tx8.wait();

  // Insurance: authorize deployer
  const tx9 = await insurance.setProtocolAuthorized(deployer.address, true);
  await tx9.wait();

  console.log("   ✓ Cross-references set\n");

  // ── Verify on Snowtrace ───────────────────────────────────────
  if (networkName !== "hardhat" && networkName !== "localhost") {
    console.log("   Verifying on Snowtrace...");
    const constructorArgs = {
      AgentRegistry:    [],
      Treasury:         [],
      FreezeSlash:      [registryAddr],
      ReputationEngine: [registryAddr],
      InsurancePool:    [],
      ExecutionWallet:  [registryAddr, treasuryAddr],
    };

    for (const [name, addr] of Object.entries(addresses)) {
      try {
        const args = constructorArgs[name] || [];
        await hre.run("verify:verify", { address: addr, constructorArguments: args });
        console.log(`   ✓ ${name} verified`);
      } catch (e) {
        if (e.message && e.message.includes("already verified")) {
          console.log(`   ✓ ${name} already verified`);
        } else {
          console.warn(`   ⚠ ${name} verification skipped: ${e.message?.slice(0, 120)}`);
        }
      }
    }
  }

  // ── Final summary ─────────────────────────────────────────────
  const explorerBase = networkName === "mainnet"
    ? "https://snowtrace.io/address"
    : "https://testnet.snowtrace.io/address";

  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("  AVAIRA Protocol Deployment Complete");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  for (const [name, addr] of Object.entries(addresses)) {
    console.log(`  ${name.padEnd(20)} ${addr}`);
    console.log(`  ${"".padEnd(20)} ${explorerBase}/${addr}`);
  }

  // Write final deployment file with metadata
  const finalDeployment = {
    network: networkName,
    chainId: hre.network.config.chainId || 43113,
    deployer: deployer.address,
    ...addresses,
    trustPoolWallet: trustWallet,
    protocolRevenueWallet: revWallet,
    permitSigner,
    deployedAt: new Date().toISOString(),
  };
  fs.writeFileSync(deploymentsFile, JSON.stringify(finalDeployment, null, 2));
  console.log(`\n  Saved to ${deploymentsFile}`);
  console.log("");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
