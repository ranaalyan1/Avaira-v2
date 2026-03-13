require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const privateKey = process.env.PROTOCOL_PRIVATE_KEY || "";
const hasValidPrivateKey = /^0x[a-fA-F0-9]{64}$/.test(privateKey);

module.exports = {
  solidity: "0.8.20",
  networks: {
    fuji: {
      url: "https://api.avax-test.network/ext/bc/C/rpc",
      chainId: 43113,
      accounts: hasValidPrivateKey ? [privateKey] : [],
    },
  },
};
