from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

# Core Trust Engine Imports
from core.intent_logger import IntentLogger
from core.validator import AvairaValidator
from core.slash_engine import SlashEngine
from core.reputation import ReputationEngine
from core.agent_vault import AgentVault
from core.sentinel import AvairaSentinel
from core.zk_vault import ZKAuditVault
from core.ape_engine import AutonomousPolicyEvolution
from core.tee_identity import TEEIdentityManager
from core.marketplace import TrustMarketplace

class Container:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncIOMotorClient(self.settings.MONGO_URL, serverSelectionTimeoutMS=3000)
        self.db = self.client[self.settings.DB_NAME]

        # Initialize Core Engines
        self.intent_logger = IntentLogger(db_client=self.db)
        self.avaira_validator = AvairaValidator()
        self.slash_engine = SlashEngine(db_client=self.db)
        self.reputation_engine = ReputationEngine(db_client=self.db)
        self.agent_vault = AgentVault()
        self.avaira_sentinel = AvairaSentinel(db_client=self.db)
        self.zk_vault = ZKAuditVault()
        self.ape_engine = AutonomousPolicyEvolution(db_client=self.db)
        self.tee_identity_manager = TEEIdentityManager()
        self.trust_marketplace = TrustMarketplace(db_client=self.db)

container = Container()
