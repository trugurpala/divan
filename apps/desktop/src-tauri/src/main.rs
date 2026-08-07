use serde::Serialize;
use serde_json::Value;
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

fn runtime_output(output: Output) -> Result<Value, String> {
    if !output.status.success() {
        let stderr = first_line(&output.stderr);
        return Err(if stderr.is_empty() {
            format!("Divan çıkış kodu {}", output.status.code().unwrap_or(-1))
        } else {
            stderr
        });
    }
    serde_json::from_slice::<Value>(&output.stdout)
        .map_err(|error| format!("Divan JSON okunamadı: {error}"))
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
    if value.trim().is_empty() {
        Err(format!("{label} boş olamaz"))
    } else {
        Ok(value)
    }
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
    let allowed = ["verified", "previewed", "released", "observed"];
    if !allowed.contains(&target.as_str()) {
        return Err("geçersiz hedef kapısı".into());
    }
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

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            health_check,
            project_status,
            goal_start_preview
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Divan Desktop");
}
