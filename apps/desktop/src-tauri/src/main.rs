use serde::Serialize;

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
    let path = which::which(id).ok().map(|value| value.to_string_lossy().to_string());
    ToolStatus { id, available: path.is_some(), path, required }
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
    let ready = tools.iter().filter(|item| item.required).all(|item| item.available);
    RuntimeProbe { ready, tools }
}

#[tauri::command]
fn divan_capabilities() -> Capabilities {
    Capabilities {
        product: "Divan",
        api_version: 1,
        shell: "tauri-2",
        features: vec!["runtime-probe", "task-console", "approval-gate", "evidence"],
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![runtime_probe, divan_capabilities])
        .run(tauri::generate_context!())
        .expect("error while running Divan Desktop");
}
