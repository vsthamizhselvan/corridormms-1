use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressEventPayload {
    pub job_id: String,
    pub processed_frames: u64,
    pub total_frames: u64,
    pub percentage: f64,
    pub fps: f64,
    pub eta_seconds: f64,
    pub current_stage: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobCompletedPayload {
    pub job_id: String,
    pub outputs: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorEventPayload {
    pub job_id: Option<String>,
    pub code: String,
    pub message: String,
}
