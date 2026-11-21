use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const PROTOCOL_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineCommand {
    #[serde(rename = "type")]
    pub command_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub command_id: Option<String>,
    #[serde(default)]
    pub payload: Value,
    pub protocol_version: u32,
}

impl EngineCommand {
    pub fn new(command_type: &str, command_id: Option<String>, payload: Value) -> Self {
        Self {
            command_type: command_type.to_string(),
            command_id,
            payload,
            protocol_version: PROTOCOL_VERSION,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineEvent {
    #[serde(rename = "type")]
    pub event_type: String,
    #[serde(default = "default_protocol_version")]
    pub protocol_version: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub command_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub job_id: Option<String>,
    #[serde(default)]
    pub data: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_code: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_message: Option<String>,
}

fn default_protocol_version() -> u32 {
    PROTOCOL_VERSION
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobConfigPayload {
    pub job_id: String,
    pub input_path: String,
    pub output_dir: String,
    pub outputs: Vec<String>,
    pub hann_chunk: u32,
    pub hann_stride: u32,
    pub low_vram: bool,
    pub despill_strength: f64,
    pub hint_first_frame: Option<String>,
    pub hint_video: Option<String>,
    pub hint_quality: f64,
    pub device: String,
    pub output_format: String,
}
