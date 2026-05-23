const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AVAIRA Protocol", function () {
  async function deployFixture() {
    const [owner, agent, target, other] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();

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
    await (await registry.setProtocol(owner.address, true)).wait();
    await (await treasury.setExecutionWallet(await executionWallet.getAddress())).wait();
    await (await treasury.setSplitWallets(owner.address, owner.address)).wait();
    await (await executionWallet.setPermitSigner(owner.address)).wait();
    await (await freezeSlash.setProtocolAuthorized(owner.address, true)).wait();
    await (await reputationEngine.setProtocolAuthorized(owner.address, true)).wait();
    await (await insurancePool.setProtocolAuthorized(owner.address, true)).wait();

    const envelope = {
      maxTxValue: ethers.parseEther("1"),
      maxSlippage: 5,
      allowedActions: "transfer,swap",
    };

    await (await registry.connect(agent).register("Alpha Agent", envelope, { value: ethers.parseEther("0.1") })).wait();

    return { owner, agent, target, other, registry, treasury, executionWallet, freezeSlash, reputationEngine, insurancePool, envelope, chainId: Number(network.chainId) };
  }

  it("registers an agent with 0.1 AVAX collateral", async function () {
    const { registry, agent } = await deployFixture();
    const agentData = await registry.getAgent(agent.address);
    expect(agentData.wallet).to.equal(agent.address);
    expect(agentData.collateral).to.equal(ethers.parseEther("0.1"));
  });

  it("generates and verifies an EIP-712 permit", async function () {
    const { agent, target, other, executionWallet, chainId } = await deployFixture();
    const deadline = Math.floor(Date.now() / 1000) + 300;
    const permit = {
      agent: agent.address,
      action: "transfer",
      target: target.address,
      value: ethers.parseEther("0.25"),
      nonce: 1,
      deadline,
    };
    const domain = {
      name: "AvairaProtocol",
      version: "1",
      chainId,
      verifyingContract: await executionWallet.getAddress(),
    };
    const types = {
      ExecutionPermit: [
        { name: "agent", type: "address" },
        { name: "action", type: "string" },
        { name: "target", type: "address" },
        { name: "value", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
      ],
    };
    const signature = await agent.signTypedData(domain, types, permit);
    const digest = await executionWallet.permitDigest(permit);
    expect(await executionWallet.usedPermits(digest)).to.equal(false);

    await expect(
      executionWallet.connect(other).execute(permit, signature, "0x", { value: permit.value })
    ).not.to.be.reverted;

    expect(await executionWallet.usedPermits(digest)).to.equal(true);
  });

  it("rejects a transaction that exceeds the risk envelope", async function () {
    const { agent, target, executionWallet, chainId } = await deployFixture();
    const deadline = Math.floor(Date.now() / 1000) + 300;
    const permit = {
      agent: agent.address,
      action: "transfer",
      target: target.address,
      value: ethers.parseEther("2"),
      nonce: 1,
      deadline,
    };
    const domain = {
      name: "AvairaProtocol",
      version: "1",
      chainId,
      verifyingContract: await executionWallet.getAddress(),
    };
    const types = {
      ExecutionPermit: [
        { name: "agent", type: "address" },
        { name: "action", type: "string" },
        { name: "target", type: "address" },
        { name: "value", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
      ],
    };
    const signature = await agent.signTypedData(domain, types, permit);
    await expect(
      executionWallet.execute(permit, signature, "0x", { value: permit.value })
    ).to.be.revertedWithCustomError(executionWallet, "ExecutionWallet__RiskEnvelopeViolation");
  });

  it("freezes and slashes an agent", async function () {
    const { agent, registry, freezeSlash } = await deployFixture();
    await (await freezeSlash.freezeAndSlash(agent.address, ethers.parseEther("0.05"), "risk deviation")).wait();
    const agentData = await registry.getAgent(agent.address);
    expect(agentData.status).to.equal(2n);
    expect(agentData.collateral).to.equal(ethers.parseEther("0.05"));
  });

  it("updates reputation through registry protocol hooks", async function () {
    const { agent, target, registry, executionWallet, chainId } = await deployFixture();
    const deadline = Math.floor(Date.now() / 1000) + 300;
    const permit = {
      agent: agent.address,
      action: "transfer",
      target: target.address,
      value: ethers.parseEther("0.2"),
      nonce: 1,
      deadline,
    };
    const domain = {
      name: "AvairaProtocol",
      version: "1",
      chainId,
      verifyingContract: await executionWallet.getAddress(),
    };
    const types = {
      ExecutionPermit: [
        { name: "agent", type: "address" },
        { name: "action", type: "string" },
        { name: "target", type: "address" },
        { name: "value", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
      ],
    };
    const signature = await agent.signTypedData(domain, types, permit);
    await executionWallet.execute(permit, signature, "0x", { value: permit.value });

    const agentData = await registry.getAgent(agent.address);
    expect(agentData.reputationScore).to.equal(2n);
    expect(agentData.nonce).to.equal(1n);
  });

  it("computes Avaira Score and grade", async function () {
    const { agent, target, executionWallet, reputationEngine, chainId } = await deployFixture();
    const deadline = Math.floor(Date.now() / 1000) + 300;
    const permit = {
      agent: agent.address,
      action: "transfer",
      target: target.address,
      value: ethers.parseEther("0.25"),
      nonce: 1,
      deadline,
    };
    const domain = {
      name: "AvairaProtocol",
      version: "1",
      chainId,
      verifyingContract: await executionWallet.getAddress(),
    };
    const types = {
      ExecutionPermit: [
        { name: "agent", type: "address" },
        { name: "action", type: "string" },
        { name: "target", type: "address" },
        { name: "value", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
      ],
    };
    const signature = await agent.signTypedData(domain, types, permit);
    await executionWallet.execute(permit, signature, "0x", { value: permit.value });

    const score = await reputationEngine.computeAvairaScore(agent.address);
    expect(score[0]).to.be.greaterThan(0n);
    expect(["A+", "A", "B", "C", "D"]).to.include(score[1]);
  });
});