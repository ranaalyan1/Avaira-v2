use tonic::{transport::Server, Request, Response, Status};
use avaira_trust_v1::trust_engine_server::{TrustEngine, TrustEngineServer};
use avaira_trust_v1::{
    ValidateIntentRequest, ValidateIntentResponse,
    LogIntentRequest, LogIntentResponse,
    GetAvairaScoreRequest, GetAvairaScoreResponse,
};
use avaira_rust_core::{AvairaCore, Intent as CoreIntent, RiskEnvelope as CoreEnvelope};

pub mod avaira_trust_v1 {
    tonic::include_proto!("avaira.trust.v1");
}

pub struct MyTrustEngine {
    core: AvairaCore,
}

#[tonic::async_trait]
impl TrustEngine for MyTrustEngine {
    async fn validate_intent(
        &self,
        request: Request<ValidateIntentRequest>,
    ) -> Result<Response<ValidateIntentResponse>, Status> {
        let req = request.into_inner();
        let intent = req.intent.ok_or_else(|| Status::invalid_argument("missing intent"))?;
        let envelope = req.envelope.ok_or_else(|| Status::invalid_argument("missing envelope"))?;

        let core_intent = CoreIntent {
            action: intent.action,
            target: intent.target,
            value_usd: intent.value_usd,
            timestamp: chrono::Utc::now(),
        };

        let core_envelope = CoreEnvelope {
            max_spend_usd: envelope.max_spend_usd,
            allowed_actions: envelope.allowed_actions,
            blocked_actions: envelope.blocked_actions,
            max_concurrent_tasks: 1,
        };

        match self.core.validate_intent(&core_intent, &core_envelope) {
            Ok(_) => Ok(Response::new(ValidateIntentResponse {
                valid: true,
                error_message: "".to_string(),
            })),
            Err(e) => Ok(Response::new(ValidateIntentResponse {
                valid: false,
                error_message: e,
            })),
        }
    }

    async fn log_intent(
        &self,
        _request: Request<LogIntentRequest>,
    ) -> Result<Response<LogIntentResponse>, Status> {
        Ok(Response::new(LogIntentResponse {
            intent_hash: "todo".to_string(),
            merkle_root: "todo".to_string(),
        }))
    }

    async fn get_avaira_score(
        &self,
        _request: Request<GetAvairaScoreRequest>,
    ) -> Result<Response<GetAvairaScoreResponse>, Status> {
        Ok(Response::new(GetAvairaScoreResponse {
            score: 85.0,
            grade: "A".to_string(),
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let trust_engine = MyTrustEngine {
        core: AvairaCore::new("secret".to_string()),
    };

    println!("Avaira gRPC Trust Engine listening on {}", addr);

    Server::builder()
        .add_service(TrustEngineServer::new(trust_engine))
        .serve(addr)
        .await?;

    Ok(())
}
