import fs from "node:fs";
import path from "node:path";
import { spawn, execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { ethers } = require("../contracts/node_modules/ethers");
const { MongoMemoryServer } = require("../contracts/node_modules/mongodb-memory-server-core");

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, "..");
const BACKEND_DIR = path.join(ROOT_DIR, "backend");
const DEPLOYMENT_PATH = path.join(ROOT_DIR, "deployments", "fuji.json");
const BACKEND_BASE_URL = process.env.SMOKE_BACKEND_URL || "http://127.0.0.1:8001";

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return;
  }
  const contents = fs.readFileSync(filePath, "utf8");
  for (const rawLine of contents.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const separatorIndex = line.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }
    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

function logResult(step, ok, detail) {
  const prefix = ok ? "PASS" : "FAIL";
  console.log(`[${prefix}] ${step}: ${detail}`);
}

function fail(step, detail) {
  logResult(step, false, detail);
  process.exitCode = 1;
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function runPythonJson(code, extraEnv = {}) {
  const output = execFileSync("python", ["-c", code], {
    cwd: ROOT_DIR,
    env: { ...process.env, ...extraEnv },
    encoding: "utf8",
  }).trim();
  return output ? JSON.parse(output) : null;
}

function canPingMongo(mongoUrl) {
  try {
    const ping = runPythonJson(
      "import json, os\nfrom pymongo import MongoClient\nclient = MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000)\nping = client.admin.command('ping')\nprint(json.dumps({'ok': ping.get('ok', 0)}))",
      { MONGO_URL: mongoUrl },
    );
    return ping?.ok === 1;
  } catch (_error) {
    return false;
  }
}

function isLocalMongoUrl(mongoUrl) {
  return /^mongodb:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(mongoUrl);
}

async function resolveMongoConfig() {
  const dbName = process.env.DB_NAME || "avaira";
  const configuredUrl = process.env.MONGO_URL?.trim();

  if (configuredUrl && canPingMongo(configuredUrl)) {
    return {
      dbName,
      mongoUrl: configuredUrl,
      mongoServer: null,
      detail: "Connected and ping returned ok=1",
    };
  }

  if (configuredUrl && !isLocalMongoUrl(configuredUrl)) {
    throw new Error(`Configured MONGO_URL is unreachable: ${configuredUrl}`);
  }

  const mongoCacheDir = path.join(ROOT_DIR, ".tmp-mongo");
  fs.mkdirSync(mongoCacheDir, { recursive: true });
  process.env.MONGOMS_DOWNLOAD_DIR = process.env.MONGOMS_DOWNLOAD_DIR || mongoCacheDir;

  const mongoServer = await MongoMemoryServer.create({
    instance: { dbName },
    binary: { downloadDir: mongoCacheDir },
  });
  const mongoUrl = mongoServer.getUri(dbName);

  if (!canPingMongo(mongoUrl)) {
    await mongoServer.stop();
    throw new Error("Ephemeral MongoDB started but failed ping check");
  }

  process.env.MONGO_URL = mongoUrl;
  return {
    dbName,
    mongoUrl,
    mongoServer,
    detail: `Started ephemeral MongoDB at ${mongoUrl}`,
  };
}

function isRealTxHash(txHash) {
  return typeof txHash === "string" && /^0x[a-fA-F0-9]{64}$/.test(txHash);
}

async function waitForBackendReady(baseUrl, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "backend not started";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/api/`);
      if (response.ok) {
        return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error.message;
    }
    await delay(1000);
  }
  throw new Error(`Backend readiness check failed: ${lastError}`);
}

async function main() {
  loadEnvFile(path.join(BACKEND_DIR, ".env"));
  loadEnvFile(path.join(ROOT_DIR, ".env"));

  const requiredVars = ["DB_NAME", "FUJI_RPC_URL", "PROTOCOL_PRIVATE_KEY", "PERMIT_SECRET"];
  for (const name of requiredVars) {
    requireEnv(name);
  }

  const { mongoUrl, dbName, mongoServer, detail: mongoDetail } = await resolveMongoConfig();

  if (!fs.existsSync(DEPLOYMENT_PATH)) {
    throw new Error(`Missing deployment file: ${DEPLOYMENT_PATH}`);
  }

  const deployment = JSON.parse(fs.readFileSync(DEPLOYMENT_PATH, "utf8"));
  const requiredContracts = ["AgentRegistry", "ExecutionWallet", "FreezeSlash", "Treasury", "ReputationEngine", "InsurancePool"];
  for (const contractName of requiredContracts) {
    if (!deployment[contractName]) {
      throw new Error(`Deployment file missing ${contractName}`);
    }
  }

  const provider = new ethers.JsonRpcProvider(process.env.FUJI_RPC_URL);
  const protocolWallet = new ethers.Wallet(process.env.PROTOCOL_PRIVATE_KEY, provider);
  const executionValue = Number(process.env.SMOKE_EXECUTION_VALUE || "0.01");
  const configuredAgentWallet = process.env.SMOKE_AGENT_WALLET?.trim();
  const agentAddress = configuredAgentWallet || ethers.Wallet.createRandom().address;
  const uniqueSuffix = Date.now();
  const agentName = `SmokeAgent-${uniqueSuffix}`;
  const agentId = `smoke-${uniqueSuffix}`;

  const registryAbi = [
    "function registerFor(address agent, string name, tuple(uint256 maxTxValue,uint8 maxSlippage,string allowedActions) envelope) payable",
    "function getAgent(address agent) view returns (tuple(address wallet,string name,uint256 collateral,uint8 status,int256 reputationScore,uint256 registeredAt,uint256 nonce,tuple(uint256 maxTxValue,uint8 maxSlippage,string allowedActions) envelope))",
  ];
  const reputationAbi = [
    "function computeAvairaScore(address agent) view returns (uint256 score, string grade)",
  ];

  const registry = new ethers.Contract(deployment.AgentRegistry, registryAbi, protocolWallet);
  const reputationEngine = new ethers.Contract(deployment.ReputationEngine, reputationAbi, provider);

  const backendEnv = {
    ...process.env,
    MONGO_URL: mongoUrl,
    DB_NAME: dbName,
    AGENT_REGISTRY_ADDRESS: deployment.AgentRegistry,
    EXECUTION_WALLET_ADDRESS: deployment.ExecutionWallet,
    FREEZE_SLASH_ADDRESS: deployment.FreezeSlash,
    TREASURY_ADDRESS: deployment.Treasury,
    REPUTATION_ENGINE_ADDRESS: deployment.ReputationEngine,
    INSURANCE_POOL_ADDRESS: deployment.InsurancePool,
    FUJI_AGENT_REGISTRY_ADDRESS: deployment.AgentRegistry,
    FUJI_EXECUTION_WALLET_ADDRESS: deployment.ExecutionWallet,
    FUJI_FREEZE_SLASH_ADDRESS: deployment.FreezeSlash,
    FUJI_TREASURY_ADDRESS: deployment.Treasury,
    FUJI_REPUTATION_ENGINE_ADDRESS: deployment.ReputationEngine,
    FUJI_INSURANCE_POOL_ADDRESS: deployment.InsurancePool,
  };

  const serverProcess = spawn(
    "python",
    ["-m", "uvicorn", "backend.server:app", "--host", "127.0.0.1", "--port", "8001"],
    {
      cwd: ROOT_DIR,
      env: backendEnv,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  serverProcess.stdout.on("data", (chunk) => process.stdout.write(chunk.toString()));
  serverProcess.stderr.on("data", (chunk) => process.stderr.write(chunk.toString()));

  let hadFailure = false;
  try {
    const network = await provider.getNetwork();
    if (Number(network.chainId) !== 43113) {
      throw new Error(`Unexpected chainId ${network.chainId}; expected 43113`);
    }
    logResult("Fuji RPC", true, `Connected to chainId ${network.chainId}`);

    logResult("MongoDB", true, mongoDetail);

    const beforeScore = await reputationEngine.computeAvairaScore(agentAddress);
    logResult("Reputation baseline", true, `Score ${beforeScore[0].toString()} / Grade ${beforeScore[1]}`);

    const envelope = {
      maxTxValue: ethers.parseEther("1.0"),
      maxSlippage: 5,
      allowedActions: "transfer,swap,stake",
    };
    const existingAgent = await registry.getAgent(agentAddress);
    if (existingAgent.wallet === ethers.ZeroAddress) {
      const registrationTx = await registry.registerFor(agentAddress, agentName, envelope, {
        value: ethers.parseEther("0.1"),
      });
      const registrationReceipt = await registrationTx.wait();
      if (Number(registrationReceipt.status) !== 1) {
        throw new Error("Agent registration transaction reverted");
      }
      logResult("Agent registration", true, `Registered ${agentAddress} with tx ${registrationReceipt.hash}`);
    } else {
      logResult("Agent registration", true, `Reused existing registered agent ${agentAddress}`);
    }

    runPythonJson(
      "import json, os\nfrom datetime import datetime, timezone\nfrom pymongo import MongoClient\nclient = MongoClient(os.environ['MONGO_URL'])\ndb = client[os.environ['DB_NAME']]\nagent = {\n  'id': os.environ['SMOKE_AGENT_ID'],\n  'name': os.environ['SMOKE_AGENT_NAME'],\n  'wallet_address': os.environ['SMOKE_AGENT_WALLET'],\n  'collateral_amount': 0.1,\n  'collateral_remaining': 0.1,\n  'mission_intent': 'Live Fuji smoke test',\n  'risk_envelope': {'max_tx_value': 1.0, 'max_daily_txns': 10, 'allowed_actions': ['transfer','swap','stake'], 'max_slippage': 0.05},\n  'status': 'active',\n  'reputation': 100,\n  'total_executions': 0,\n  'successful_executions': 0,\n  'failed_executions': 0,\n  'registered_at': datetime.now(timezone.utc).isoformat(),\n  'chain_id': '43113'\n}\ndb.agents.replace_one({'id': agent['id']}, agent, upsert=True)\nprint(json.dumps({'seeded': True}))",
      {
        ...backendEnv,
        SMOKE_AGENT_ID: agentId,
        SMOKE_AGENT_NAME: agentName,
        SMOKE_AGENT_WALLET: agentAddress,
      },
    );
    logResult("Mongo seed", true, `Inserted backend agent record ${agentId}`);

    await waitForBackendReady(BACKEND_BASE_URL);
    logResult("Backend boot", true, `Backend ready at ${BACKEND_BASE_URL}`);

    const executionResponse = await fetch(`${BACKEND_BASE_URL}/api/executions/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent_id: agentId,
        action: "transfer",
        target_address: protocolWallet.address,
        value: executionValue,
        data: "0x",
        chain_id: "43113",
      }),
    });
    const executionBody = await executionResponse.json();
    if (!executionResponse.ok) {
      throw new Error(`Execution request failed (${executionResponse.status}): ${executionBody.error_message || executionBody.detail || JSON.stringify(executionBody)}`);
    }
    if (!isRealTxHash(executionBody.tx_hash)) {
      throw new Error(`Execution route did not return a real on-chain hash: ${executionBody.tx_hash || "missing"}`);
    }
    logResult("Execution request", true, `Received real tx hash ${executionBody.tx_hash}`);

    const executionReceipt = await provider.waitForTransaction(executionBody.tx_hash, 1, 60000);
    if (!executionReceipt || executionReceipt.status !== 1) {
      throw new Error(`Execution tx ${executionBody.tx_hash} was not confirmed successfully`);
    }
    logResult("Execution receipt", true, `Confirmed on-chain in block ${executionReceipt.blockNumber}`);

    const afterScore = await reputationEngine.computeAvairaScore(agentAddress);
    if (afterScore[0] <= beforeScore[0]) {
      throw new Error(`Avaira Score did not increase: before=${beforeScore[0].toString()} after=${afterScore[0].toString()}`);
    }
    logResult("ReputationEngine score", true, `Score ${beforeScore[0].toString()} -> ${afterScore[0].toString()} (${afterScore[1]})`);
  } catch (error) {
    hadFailure = true;
    fail("Smoke test", error.message || String(error));
  } finally {
    serverProcess.kill("SIGTERM");
    try {
      await delay(1000);
    } catch (error) {
      // ignore cleanup wait errors
    }
    if (mongoServer) {
      await mongoServer.stop();
    }
  }

  if (hadFailure) {
    process.exit(1);
  }
}

main().catch((error) => {
  fail("Smoke test", error.message || String(error));
  process.exit(1);
});