use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RiskEnvelope {
    pub max_spend_usd: f64,
    pub allowed_actions: Vec<String>,
    pub blocked_actions: Vec<String>,
    pub max_concurrent_tasks: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Intent {
    pub action: String,
    pub target: String,
    pub value_usd: f64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LogEntry {
    pub id: String,
    pub agent_id: String,
    pub intent_hash: String,
    pub prev_hash: String,
    pub merkle_root: String,
    pub timestamp: DateTime<Utc>,
}

pub struct AvairaCore {
    pub secret: String,
}

impl AvairaCore {
    pub fn new(secret: String) -> Self {
        Self { secret }
    }

    pub fn compute_intent_hash(&self, intent: &Intent, agent_id: &str, prev_hash: &str) -> String {
        let mut hasher = Sha256::new();
        let payload = format!(
            "{}{}{}{}{}",
            intent.action, intent.target, intent.value_usd, agent_id, prev_hash
        );
        hasher.update(payload.as_bytes());
        hex::encode(hasher.finalize())
    }

    pub fn validate_intent(&self, intent: &Intent, envelope: &RiskEnvelope) -> Result<bool, String> {
        if intent.value_usd > envelope.max_spend_usd {
            return Err(format!(
                "Spend limit exceeded: {} > {}",
                intent.value_usd, envelope.max_spend_usd
            ));
        }
        if envelope.blocked_actions.contains(&intent.action) {
            return Err(format!("Action '{}' is explicitly blocked", intent.action));
        }
        if !envelope.allowed_actions.is_empty() && !envelope.allowed_actions.contains(&intent.action) {
            return Err(format!("Action '{}' is not in allowed list", intent.action));
        }
        Ok(true)
    }

    pub fn calculate_score(&self, metrics: HashMap<String, f64>) -> f64 {
        let success_rate = metrics.get("success_rate").unwrap_or(&0.0);
        let consistency = metrics.get("consistency").unwrap_or(&0.0);
        let slash_penalty = metrics.get("slash_penalty").unwrap_or(&0.0);
        let volume = metrics.get("volume").unwrap_or(&0.0);
        let maturity = metrics.get("maturity").unwrap_or(&0.0);
        let appeal = metrics.get("appeal").unwrap_or(&0.0);

        let score = 0.30 * success_rate + 0.20 * consistency - 0.20 * slash_penalty
                  + 0.15 * volume + 0.10 * maturity + 0.05 * appeal;

        score.clamp(0.0, 100.0)
    }
}

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyclass]
pub struct PyAvairaCore {
    inner: AvairaCore,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyAvairaCore {
    #[new]
    fn new(secret: String) -> Self {
        Self {
            inner: AvairaCore::new(secret),
        }
    }

    fn calculate_score(&self, metrics: HashMap<String, f64>) -> f64 {
        self.inner.calculate_score(metrics)
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn avaira_rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyAvairaCore>()?;
    Ok(())
}

#[cfg(test)]
mod tests;
