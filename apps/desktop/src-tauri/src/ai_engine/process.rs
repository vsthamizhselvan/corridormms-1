use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::{oneshot, Mutex};

use super::protocol::{EngineCommand, EngineEvent};

pub struct AiProcessManager {
    child: Mutex<Option<Child>>,
    stdin: Mutex<Option<ChildStdin>>,
    pending_commands: Arc<Mutex<HashMap<String, oneshot::Sender<EngineEvent>>>>,
    app_handle: AppHandle,
    is_ready: Arc<Mutex<bool>>,
}

impl AiProcessManager {
    pub fn new(app_handle: AppHandle) -> Self {
        Self {
            child: Mutex::new(None),
            stdin: Mutex::new(None),
            pending_commands: Arc::new(Mutex::new(HashMap::new())),
            app_handle,
            is_ready: Arc::new(Mutex::new(false)),
        }
    }

    /// Resolves the Python executable path, prioritizing project virtualenv.
    pub fn resolve_python_path() -> PathBuf {
        let candidates = [
            PathBuf::from(".venv/bin/python3"),
            PathBuf::from(".venv/bin/python"),
            PathBuf::from(".venv/Scripts/python.exe"),
            PathBuf::from("/opt/homebrew/bin/python3.11"),
            PathBuf::from("/opt/homebrew/opt/python@3.11/bin/python3.11"),
            PathBuf::from("python3"),
            PathBuf::from("python"),
        ];

        for c in &candidates {
            if c.is_file() {
                return c.clone();
            }
        }
        PathBuf::from("python3")
    }

    /// Resolves the engine entry script.
    pub fn resolve_script_path() -> PathBuf {
        let candidates = [
            PathBuf::from("engine/desktop_api/main.py"),
            PathBuf::from("../../../engine/desktop_api/main.py"),
            PathBuf::from("../../engine/desktop_api/main.py"),
        ];

        for c in &candidates {
            if c.is_file() {
                return c.clone();
            }
        }
        PathBuf::from("engine/desktop_api/main.py")
    }

    /// Starts the Python worker subprocess.
    pub async fn start(&self) -> Result<(), String> {
        let mut child_guard = self.child.lock().await;
        if child_guard.is_some() {
            return Ok(()); // Already running
        }

        let py_bin = Self::resolve_python_path();
        let script = Self::resolve_script_path();

        eprintln!(
            "[AiEngine] Launching Python AI Worker: {} {}",
            py_bin.display(),
            script.display()
        );

        let mut cmd = Command::new(py_bin);
        cmd.arg(&script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = cmd
            .spawn()
            .map_err(|e| format!("Failed to spawn Python AI engine: {}", e))?;

        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| "Failed to capture stdin of AI worker".to_string())?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| "Failed to capture stdout of AI worker".to_string())?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| "Failed to capture stderr of AI worker".to_string())?;

        *self.stdin.lock().await = Some(stdin);
        *child_guard = Some(child);

        let pending_map = self.pending_commands.clone();
        let app = self.app_handle.clone();
        let is_ready = self.is_ready.clone();

        // 1. Stdout reader task
        tokio::spawn(async move {
            let mut reader = BufReader::new(stdout).lines();
            while let Ok(Some(line)) = reader.next_line().await {
                let trimmed = line.trim();
                if trimmed.is_empty() {
                    continue;
                }

                match serde_json::from_str::<EngineEvent>(trimmed) {
                    Ok(event) => {
                        if event.event_type == "ready" {
                            *is_ready.lock().await = true;
                        }

                        // Check if this event completes a pending request
                        if let Some(cmd_id) = &event.command_id {
                            let mut map = pending_map.lock().await;
                            if let Some(sender) = map.remove(cmd_id) {
                                let _ = sender.send(event.clone());
                            }
                        }

                        // Emit Tauri event to React frontend
                        let _ = app.emit("ai-event", &event);

                        if event.event_type == "progress" {
                            let _ = app.emit("ai-progress", &event.data);
                        } else if event.event_type == "job_completed" {
                            let _ = app.emit("ai-job-completed", &event.data);
                        } else if event.event_type == "error" {
                            let _ = app.emit("ai-error", &event);
                        }
                    }
                    Err(err) => {
                        eprintln!("[AiEngine Raw Stdout] {}: (parse error: {})", trimmed, err);
                    }
                }
            }
            eprintln!("[AiEngine] Worker stdout closed.");
            *is_ready.lock().await = false;
        });

        // 2. Stderr logger task
        tokio::spawn(async move {
            let mut reader = BufReader::new(stderr).lines();
            while let Ok(Some(line)) = reader.next_line().await {
                eprintln!("[AiEngine Stderr] {}", line);
            }
        });

        Ok(())
    }

    /// Sends a command to the Python worker and waits for a response matching command_id.
    pub async fn send_command_and_wait(
        &self,
        command_type: &str,
        payload: serde_json::Value,
        timeout_secs: u64,
    ) -> Result<EngineEvent, String> {
        self.ensure_running().await?;

        let command_id = format!("cmd_{}_{}", command_type, uuid::Uuid::new_v4());
        let (tx, rx) = oneshot::channel();

        {
            let mut pending = self.pending_commands.lock().await;
            pending.insert(command_id.clone(), tx);
        }

        let cmd = EngineCommand::new(command_type, Some(command_id.clone()), payload);
        let json_line = serde_json::to_string(&cmd)
            .map_err(|e| format!("Failed to serialize command: {}", e))?
            + "\n";

        {
            let mut stdin_guard = self.stdin.lock().await;
            if let Some(ref mut stdin) = *stdin_guard {
                stdin
                    .write_all(json_line.as_bytes())
                    .await
                    .map_err(|e| format!("Failed to write to worker stdin: {}", e))?;
                stdin
                    .flush()
                    .await
                    .map_err(|e| format!("Failed to flush worker stdin: {}", e))?;
            } else {
                return Err("Worker stdin is not available".to_string());
            }
        }

        // Wait with timeout
        tokio::select! {
            res = rx => {
                res.map_err(|_| "Response channel closed without answer".to_string())
            }
            _ = tokio::time::sleep(tokio::time::Duration::from_secs(timeout_secs)) => {
                let mut pending = self.pending_commands.lock().await;
                pending.remove(&command_id);
                Err(format!("Command '{}' timed out after {}s", command_type, timeout_secs))
            }
        }
    }

    /// Sends a command without waiting for a synchronous response.
    pub async fn send_command(
        &self,
        command_type: &str,
        payload: serde_json::Value,
    ) -> Result<(), String> {
        self.ensure_running().await?;

        let cmd = EngineCommand::new(command_type, None, payload);
        let json_line = serde_json::to_string(&cmd)
            .map_err(|e| format!("Failed to serialize command: {}", e))?
            + "\n";

        let mut stdin_guard = self.stdin.lock().await;
        if let Some(ref mut stdin) = *stdin_guard {
            stdin
                .write_all(json_line.as_bytes())
                .await
                .map_err(|e| format!("Failed to write to worker stdin: {}", e))?;
            stdin
                .flush()
                .await
                .map_err(|e| format!("Failed to flush worker stdin: {}", e))?;
            Ok(())
        } else {
            Err("Worker stdin is not available".to_string())
        }
    }

    pub async fn ensure_running(&self) -> Result<(), String> {
        let is_running = self.child.lock().await.is_some();
        if !is_running {
            self.start().await?;
            // Give worker 200ms to initialize
            tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
        }
        Ok(())
    }

    pub async fn is_running(&self) -> bool {
        self.child.lock().await.is_some()
    }

    pub async fn stop(&self) -> Result<(), String> {
        let _ = self.send_command("shutdown", serde_json::json!({})).await;

        let mut child_guard = self.child.lock().await;
        if let Some(mut child) = child_guard.take() {
            let _ = child.kill().await;
        }
        *self.stdin.lock().await = None;
        *self.is_ready.lock().await = false;
        Ok(())
    }
}
