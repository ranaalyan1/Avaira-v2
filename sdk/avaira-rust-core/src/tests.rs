#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_score_calculation() {
        let core = AvairaCore::new("secret".to_string());
        let mut metrics = HashMap::new();
        metrics.insert("success_rate".to_string(), 100.0);
        metrics.insert("consistency".to_string(), 100.0);
        metrics.insert("slash_penalty".to_string(), 0.0);
        metrics.insert("volume".to_string(), 50.0);
        metrics.insert("maturity".to_string(), 10.0);
        metrics.insert("appeal".to_string(), 100.0);

        let score = core.calculate_score(metrics);
        // 0.3*100 + 0.2*100 - 0.2*0 + 0.15*50 + 0.1*10 + 0.05*100
        // 30 + 20 - 0 + 7.5 + 1 + 5 = 63.5
        assert_eq!(score, 63.5);
    }

    #[test]
    fn test_intent_validation() {
        let core = AvairaCore::new("secret".to_string());
        let envelope = RiskEnvelope {
            max_spend_usd: 100.0,
            allowed_actions: vec!["search".to_string()],
            blocked_actions: vec!["delete".to_string()],
            max_concurrent_tasks: 1,
        };

        let valid_intent = Intent {
            action: "search".to_string(),
            target: "google.com".to_string(),
            value_usd: 10.0,
            timestamp: Utc::now(),
        };
        assert!(core.validate_intent(&valid_intent, &envelope).is_ok());

        let expensive_intent = Intent {
            action: "search".to_string(),
            target: "google.com".to_string(),
            value_usd: 200.0,
            timestamp: Utc::now(),
        };
        assert!(core.validate_intent(&expensive_intent, &envelope).is_err());

        let blocked_intent = Intent {
            action: "delete".to_string(),
            target: "database".to_string(),
            value_usd: 0.0,
            timestamp: Utc::now(),
        };
        assert!(core.validate_intent(&blocked_intent, &envelope).is_err());
    }
}
