use serde::Serialize;
use serde_json::{json, Value};
use std::env;
use std::path::PathBuf;
use std::process::{Command, Output};
use tauri::Manager;

const MAX_DETAIL: usize = 240;

#[derive(Debug, Serialize)]
struct ToolProbe {
    id: &'static str,
    label: &'static str,
    available: bool,
    detail: String,
}

#[derive(Debug, Serialize)]
struct HealthSnapshot {
    schema_version: u8,
    status: &'static str,
    tools: Vec<ToolProbe>,
}

#[cfg(target_os = "windows")]
fn hide_console_window(command: &mut Command) {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    command.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(target_os = "windows"))]
fn hide_console_window(_command: &mut Command) {}

fn execute(program: &str, args: &[&str]) -> Result<Output, String> {
    let mut command = Command::new(program);
    command.args(args);
    hide_console_window(&mut command);
    command.output().map_err(|error| error.to_string())
}

fn first_line(bytes: &[u8]) -> String {
    let text = String::from_utf8_lossy(bytes);
    let compact = text.lines().next().unwrap_or_default().trim();
    compact.chars().take(MAX_DETAIL).collect()
}

fn probe(id: &'static str, label: &'static str, candidates: &[(&str, &[&str])]) -> ToolProbe {
    let mut last_error = String::new();
    for (program, args) in candidates {
        match execute(program, args) {
            Ok(output) if output.status.success() => {
                let stdout = first_line(&output.stdout);
                let stderr = first_line(&output.stderr);
                return ToolProbe {
                    id,
                    label,
                    available: true,
                    detail: if !stdout.is_empty() {
                        stdout
                    } else if !stderr.is_empty() {
                        stderr
                    } else {
                        "hazır".into()
                    },
                };
            }
            Ok(output) => {
                let stderr = first_line(&output.stderr);
                last_error = if stderr.is_empty() {
                    format!("çıkış kodu {}", output.status.code().unwrap_or(-1))
                } else {
                    stderr
                };
            }
            Err(error) => last_error = error,
        }
    }
    ToolProbe {
        id,
        label,
        available: false,
        detail: if last_error.is_empty() {
            "bulunamadı".into()
        } else {
            last_error
        },
    }
}

fn probe_orca() -> ToolProbe {
    match execute("orca", &["status", "--json"]) {
        Ok(output) if output.status.success() => ToolProbe {
            id: "orca",
            label: "Orca Runtime",
            available: true,
            detail: "status hazır".into(),
        },
        Ok(output) => ToolProbe {
            id: "orca",
            label: "Orca Runtime",
            available: false,
            detail: {
                let stderr = first_line(&output.stderr);
                if stderr.is_empty() {
                    "status başarısız".into()
                } else {
                    stderr
                }
            },
        },
        Err(error) => ToolProbe {
            id: "orca",
            label: "Orca Runtime",
            available: false,
            detail: error,
        },
    }
}

fn resource_candidates(app: &tauri::AppHandle, filename: &str) -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push(resource_dir.join("resources").join(filename));
        candidates.push(resource_dir.join(filename));
    }
    candidates.push(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("resources")
            .join(filename),
    );
    candidates.push(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("..")
            .join("dist")
            .join(filename),
    );
    candidates
}

fn runtime_exe_candidates(app: &tauri::AppHandle) -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(explicit) = env::var("DIVAN_RUNTIME_EXE") {
        if !explicit.trim().is_empty() {
            candidates.push(PathBuf::from(explicit));
        }
    }
    candidates.extend(resource_candidates(app, "divan-runtime.exe"));
    candidates
}

fn runtime_pyz_candidates(app: &tauri::AppHandle) -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(explicit) = env::var("DIVAN_PROJECT_PYZ") {
        if !explicit.trim().is_empty() {
            candidates.push(PathBuf::from(explicit));
        }
    }
    candidates.extend(resource_candidates(app, "divan-project.pyz"));
    candidates
}

fn find_runtime_exe(app: &tauri::AppHandle) -> Option<PathBuf> {
    runtime_exe_candidates(app)
        .into_iter()
        .find(|candidate| candidate.is_file())
}

fn find_runtime_pyz(app: &tauri::AppHandle) -> Option<PathBuf> {
    runtime_pyz_candidates(app)
        .into_iter()
        .find(|candidate| candidate.is_file())
}

fn json_error(value: &Value) -> Option<String> {
    let errors = value.get("errors")?.as_array()?;
    let messages = errors
        .iter()
        .filter_map(Value::as_str)
        .map(str::trim)
        .filter(|message| !message.is_empty())
        .collect::<Vec<_>>();
    if messages.is_empty() {
        None
    } else {
        Some(messages.join("; "))
    }
}

fn runtime_output(output: Output) -> Result<Value, String> {
    let parsed = serde_json::from_slice::<Value>(&output.stdout).ok();
    if !output.status.success() {
        if let Some(value) = parsed.as_ref() {
            if let Some(message) = json_error(value) {
                return Err(message);
            }
        }
        let stderr = first_line(&output.stderr);
        return Err(if stderr.is_empty() {
            format!("Divan çıkış kodu {}", output.status.code().unwrap_or(-1))
        } else {
            stderr
        });
    }
    parsed.ok_or_else(|| "Divan JSON okunamadı".to_string())
}

fn run_standalone_runtime(runtime: PathBuf, runtime_args: &[String]) -> Result<Value, String> {
    let mut command = Command::new(runtime);
    command.args(runtime_args);
    hide_console_window(&mut command);
    command
        .output()
        .map_err(|error| format!("Divan runtime başlatılamadı: {error}"))
        .and_then(runtime_output)
}

fn run_pyz_runtime(runtime: PathBuf, runtime_args: &[String]) -> Result<Value, String> {
    let runtime_text = runtime.to_string_lossy().to_string();
    let candidates: [(&str, &[&str]); 3] = [
        ("py", &["-3"]),
        ("python", &[]),
        ("python3", &[]),
    ];
    let mut last_error = String::new();

    for (program, prefix) in candidates {
        let mut command = Command::new(program);
        command.args(prefix);
        command.arg(&runtime_text);
        command.args(runtime_args);
        hide_console_window(&mut command);
        match command.output() {
            Ok(output) if output.status.success() => return runtime_output(output),
            Ok(output) => {
                let parsed = serde_json::from_slice::<Value>(&output.stdout).ok();
                if let Some(value) = parsed.as_ref() {
                    if let Some(message) = json_error(value) {
                        last_error = message;
                        continue;
                    }
                }
                let stderr = first_line(&output.stderr);
                last_error = if stderr.is_empty() {
                    format!("Divan çıkış kodu {}", output.status.code().unwrap_or(-1))
                } else {
                    stderr
                };
            }
            Err(error) => last_error = error.to_string(),
        }
    }
    Err(if last_error.is_empty() {
        "Python 3 çalıştırıcısı bulunamadı.".into()
    } else {
        last_error
    })
}

fn run_runtime(app: &tauri::AppHandle, runtime_args: &[String]) -> Result<Value, String> {
    if let Some(runtime) = find_runtime_exe(app) {
        return run_standalone_runtime(runtime, runtime_args);
    }
    if let Some(runtime) = find_runtime_pyz(app) {
        return run_pyz_runtime(runtime, runtime_args);
    }
    Err(
        "Divan runtime bulunamadı. Installer divan-runtime.exe içermeli; geliştirici fallback'i için DIVAN_PROJECT_PYZ kullanılabilir."
            .into(),
    )
}

fn runtime_probe(app: &tauri::AppHandle) -> ToolProbe {
    if let Some(path) = find_runtime_exe(app) {
        return ToolProbe {
            id: "divan-runtime",
            label: "Divan Runtime",
            available: true,
            detail: format!(
                "standalone · {}",
                path.file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or("divan-runtime.exe")
            ),
        };
    }
    if let Some(path) = find_runtime_pyz(app) {
        return ToolProbe {
            id: "divan-runtime",
            label: "Divan Runtime",
            available: true,
            detail: format!(
                "Python fallback · {}",
                path.file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or("divan-project.pyz")
            ),
        };
    }
    ToolProbe {
        id: "divan-runtime",
        label: "Divan Runtime",
        available: false,
        detail: "divan-runtime.exe henüz paketlenmedi".into(),
    }
}

#[tauri::command]
fn health_check(app: tauri::AppHandle) -> HealthSnapshot {
    let git = probe("git", "Git", &[("git", &["--version"])]);
    let codex = probe("codex", "Codex CLI", &[("codex", &["--version"])]);
    let claude = probe("claude", "Claude Code", &[("claude", &["--version"])]);
    let opencode = probe("opencode", "OpenCode", &[("opencode", &["--version"])]);
    let python = probe(
        "python",
        "Python 3 (opsiyonel)",
        &[
            ("py", &["-3", "--version"]),
            ("python", &["--version"]),
            ("python3", &["--version"]),
        ],
    );
    let orca = probe_orca();
    let runtime = runtime_probe(&app);
    let tools = vec![git, codex, claude, opencode, orca, runtime, python];
    let status = if tools
        .iter()
        .any(|tool| (tool.id == "git" || tool.id == "divan-runtime") && !tool.available)
    {
        "blocked"
    } else {
        "ready"
    };
    HealthSnapshot {
        schema_version: 1,
        status,
        tools,
    }
}

fn non_empty(value: String, label: &str) -> Result<String, String> {
    let normalized = value.trim().to_string();
    if normalized.is_empty() {
        Err(format!("{label} boş olamaz"))
    } else {
        Ok(normalized)
    }
}

fn bounded_argument(value: String, label: &str, max_chars: usize) -> Result<String, String> {
    let normalized = non_empty(value, label)?;
    if normalized.chars().count() > max_chars {
        return Err(format!("{label} çok uzun"));
    }
    if normalized.chars().any(|character| matches!(character, '\0' | '\r' | '\n')) {
        return Err(format!("{label} kontrol karakteri içeremez"));
    }
    Ok(normalized)
}

fn validated_target(value: String) -> Result<String, String> {
    let target = non_empty(value, "hedef kapısı")?;
    let allowed = ["verified", "previewed", "released", "observed"];
    if allowed.contains(&target.as_str()) {
        Ok(target)
    } else {
        Err("geçersiz hedef kapısı".into())
    }
}

fn required_goal_id(value: &Value) -> Result<String, String> {
    value
        .get("goal_id")
        .and_then(Value::as_str)
        .filter(|goal_id| goal_id.starts_with("goal-") && goal_id.len() == 17)
        .map(str::to_string)
        .ok_or_else(|| "Divan goal_id üretmedi".to_string())
}

#[tauri::command]
fn project_status(app: tauri::AppHandle, project: String) -> Result<Value, String> {
    let project = non_empty(project, "proje")?;
    run_runtime(
        &app,
        &[
            "project".into(),
            "status".into(),
            "--project".into(),
            project,
            "--json".into(),
        ],
    )
}

#[tauri::command]
fn goal_start_preview(
    app: tauri::AppHandle,
    project: String,
    intent: String,
    target: String,
) -> Result<Value, String> {
    let project = non_empty(project, "proje")?;
    let intent = non_empty(intent, "hedef")?;
    let target = validated_target(target)?;
    run_runtime(
        &app,
        &[
            "goal".into(),
            "start".into(),
            "--project".into(),
            project,
            "--intent".into(),
            intent,
            "--target".into(),
            target,
            "--json".into(),
        ],
    )
}

#[tauri::command]
fn approve_and_start(
    app: tauri::AppHandle,
    project: String,
    intent: String,
    target: String,
    name: String,
    agent: String,
    repo_selector: String,
) -> Result<Value, String> {
    let project = non_empty(project, "proje")?;
    let intent = bounded_argument(intent, "hedef", 32_000)?;
    let target = validated_target(target)?;
    let name = bounded_argument(name, "worktree adı", 120)?;
    let agent = bounded_argument(agent, "ajan", 120)?;
    let repo_selector = bounded_argument(repo_selector, "Orca repo selector", 240)?;
    if !repo_selector.starts_with("id:") || repo_selector.len() <= 3 {
        return Err("Orca repo selector bu alpha'da id:<repoId> biçiminde olmalı".into());
    }

    let created = run_runtime(
        &app,
        &[
            "goal".into(),
            "start".into(),
            "--project".into(),
            project.clone(),
            "--intent".into(),
            intent.clone(),
            "--target".into(),
            target.clone(),
            "--execute".into(),
            "--json".into(),
        ],
    )?;
    let goal_id = required_goal_id(&created)?;

    let preparation = run_runtime(
        &app,
        &[
            "goal".into(),
            "prepare".into(),
            "--project".into(),
            project.clone(),
            "--goal".into(),
            goal_id.clone(),
            "--execute".into(),
            "--json".into(),
        ],
    )?;

    let execution = run_runtime(
        &app,
        &[
            "engines".into(),
            "worktree-create".into(),
            "--engine".into(),
            "orca".into(),
            "--project".into(),
            project,
            "--goal".into(),
            goal_id.clone(),
            "--name".into(),
            name,
            "--repo-selector".into(),
            repo_selector,
            "--agent".into(),
            agent,
            "--prompt".into(),
            intent,
            "--setup".into(),
            "inherit".into(),
            "--execute".into(),
            "--json".into(),
        ],
    )?;

    Ok(json!({
        "schema_version": 1,
        "kind": "desktop-approval-execution",
        "status": "started",
        "goal_id": goal_id,
        "goal": created,
        "preparation": preparation,
        "execution": execution,
    }))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            health_check,
            project_status,
            goal_start_preview,
            approve_and_start
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Divan Desktop");
}
