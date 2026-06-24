from app.main import app
from app.containers import container
from app.dependencies import require_authenticated_user
from app.api.agents import register_agent, agent_run, _get_agent_from_key
from app.models.agent import AgentCreate, AgentRunRequest
from app.models.risk import RiskEnvelope

db = container.db
intent_logger = container.intent_logger
avaira_validator = container.avaira_validator
slash_engine = container.slash_engine
reputation_engine = container.reputation_engine
ape_engine = container.ape_engine
agent_vault = container.agent_vault

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
