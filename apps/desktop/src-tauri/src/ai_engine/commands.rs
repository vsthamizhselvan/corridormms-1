use std::sync::Arc;
use tauri::State;

use super::process::AiProcessManager;
use super::protocol::JobConfigPayload;

pub type AiEngineState = Arc<AiProcessManager>;

#[tauri::command]
pub async fn start_ai_engine(state: State<'_, AiEngineState>) -> Result<bool, String> {
    state.start().await?;
    Ok(true)
}

#[tauri::command]
pub async fn stop_ai_engine(state: State<'_, AiEngineState>) -> Result<bool, String> {
    state.stop().await?;
    Ok(true)
}

#[tauri::command]
pub async fn get_engine_status(state: State<'_, AiEngineState>) -> Result<serde_json::Value, String> {
    let running = state.is_running().await;
    Ok(serde_json::json!({
        "running": running,
        "engine_type": "corridorkey_v2",
        "python_path": AiProcessManager::resolve_python_path().to_string_lossy(),
    }))
}

#[tauri::command]
pub async fn detect_hardware(state: State<'_, AiEngineState>) -> Result<serde_json::Value, String> {
    let res = state
        .send_command_and_wait("detect_hardware", serde_json::json!({}), 10)
        .await?;
    Ok(res.data)
}

#[tauri::command]
pub async fn check_model_status(state: State<'_, AiEngineState>) -> Result<serde_json::Value, String> {
    let res = state
        .send_command_and_wait("check_model_status", serde_json::json!({}), 10)
        .await?;
    Ok(res.data)
}

#[tauri::command]
pub async fn load_corridor_key_model(
    state: State<'_, AiEngineState>,
    device: Option<String>,
) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({
        "device": device.unwrap_or_else(|| "auto".to_string())
    });
    let res = state
        .send_command_and_wait("load_model", payload, 60)
        .await?;
    Ok(res.data)
}

#[tauri::command]
pub async fn start_inference_job(
    state: State<'_, AiEngineState>,
    config: JobConfigPayload,
) -> Result<serde_json::Value, String> {
    let payload = serde_json::to_value(&config)
        .map_err(|e| format!("Failed to serialize job config: {}", e))?;

    let res = state
        .send_command_and_wait("start_job", payload, 15)
        .await?;
    Ok(res.data)
}

#[tauri::command]
pub async fn cancel_inference_job(
    state: State<'_, AiEngineState>,
    job_id: String,
) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({ "job_id": job_id });
    let res = state
        .send_command_and_wait("cancel_job", payload, 10)
        .await?;
    Ok(res.data)
}

#[tauri::command]
pub async fn get_job_status(
    state: State<'_, AiEngineState>,
    job_id: String,
) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({ "job_id": job_id });
    let res = state
        .send_command_and_wait("get_job_status", payload, 10)
        .await?;
    Ok(res.data)
}
