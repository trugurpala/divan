use serde::Serialize;
use tauri_plugin_shell::{process::CommandEvent, ShellExt};

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ToolStatus {
    id: &'static str,
    available: bool,
    path: Option<String>,
    required: bool,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeProbe {
    ready: bool,
    tools: Vec<ToolStatus>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Capabilities {
    product: &'static str,
    api_version: u8,
    shell: &'static str,
    features: Vec<&'static str>,
}

fn tool(id: &'static str, required: bool) -> ToolStatus {
    let path = which::which(id)
        .ok()
        .map(|value| value.to_string_lossy().to_string());
    ToolStatus {
        id,
        available: path.is_some(),
        path,
        required,
    }
}

#[tauri::command]
fn runtime_probe() -> RuntimeProbe {
    let tools = vec![
        tool("git", true),
        tool("orca", false),
        tool("codex", false),
        tool("claude", false),
        tool("opencode", false),
    ];
    let ready = tools
        .iter()
        .filter(|item| item.required)
        .all(|item| item.available);
    RuntimeProbe { ready, tools }
}

#[tauri::command]
fn divan_capabilities() -> Capabilities {
    Capabilities {
        product: "Divan",
        api_version: 1,
        shell: "tauri-2",
        features: vec![
            "runtime-probe",
            "task-console",
            "approval-gate",
            "evidence",
            "core-sidecar",
            "native-folder-picker",
        ],
    }
}

#[tauri::command]
async fn core_request(app: tauri::AppHandle, request: String) -> Result<String, String> {
    if request.trim().is_empty() {
        return Err("core request must not be empty".to_string());
    }

    let sidecar = app
        .shell()
        .sidecar("divan-core")
        .map_err(|error| error.to_string())?;
    let (mut events, mut child) = sidecar.spawn().map_err(|error| error.to_string())?;
    child
        .write(format!("{}\n", request).as_bytes())
        .map_err(|error| error.to_string())?;

    let mut stdout = Vec::<u8>::new();
    let mut stderr = Vec::<u8>::new();
    while let Some(event) = events.recv().await {
        match event {
            CommandEvent::Stdout(bytes) => stdout.extend(bytes),
            CommandEvent::Stderr(bytes) => stderr.extend(bytes),
            CommandEvent::Terminated(_) => break,
            _ => {}
        }
    }

    if stdout.is_empty() {
        let message = String::from_utf8_lossy(&stderr).trim().to_string();
        return Err(if message.is_empty() {
            "Divan Core returned no output".to_string()
        } else {
            message
        });
    }

    String::from_utf8(stdout).map_err(|error| error.to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            runtime_probe,
            divan_capabilities,
            core_request
        ])
        .run(tauri::generate_context!())
        .expect("error while running Divan Desktop");
}
