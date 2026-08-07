use serde::Serialize;
use tauri_plugin_shell::{process::CommandEvent, ShellExt};
#[cfg(feature = "signed-updater")]
use tauri_plugin_updater::{Update, UpdaterExt};

#[cfg(feature = "updater-e2e")]
mod updater_e2e;

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
    version: &'static str,
    api_version: u8,
    shell: &'static str,
    features: Vec<&'static str>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct UpdateStatus {
    available: bool,
    version: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct UpdateInstallStatus {
    installed: bool,
    version: Option<String>,
}

#[cfg(feature = "signed-updater")]
#[derive(Default)]
struct PendingUpdate(std::sync::Mutex<Option<Update>>);

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
    let mut features = vec![
        "runtime-probe",
        "task-console",
        "approval-gate",
        "evidence",
        "core-sidecar",
        "native-folder-picker",
    ];
    if cfg!(feature = "signed-updater") {
        features.push("signed-updater");
    }
    Capabilities {
        product: "Divan",
        version: env!("CARGO_PKG_VERSION"),
        api_version: 1,
        shell: "tauri-2",
        features,
    }
}

#[cfg(feature = "signed-updater")]
#[tauri::command]
async fn check_for_update(
    app: tauri::AppHandle,
    pending_update: tauri::State<'_, PendingUpdate>,
) -> Result<UpdateStatus, String> {
    {
        let mut pending = pending_update
            .0
            .lock()
            .map_err(|_| "pending updater state is unavailable".to_string())?;
        *pending = None;
    }

    let updater = app.updater().map_err(|error| error.to_string())?;
    let update = updater.check().await.map_err(|error| error.to_string())?;
    match update {
        Some(update) => {
            let version = update.version.to_string();
            let mut pending = pending_update
                .0
                .lock()
                .map_err(|_| "pending updater state is unavailable".to_string())?;
            *pending = Some(update);
            Ok(UpdateStatus {
                available: true,
                version: Some(version),
            })
        }
        None => Ok(UpdateStatus {
            available: false,
            version: None,
        }),
    }
}

#[cfg(not(feature = "signed-updater"))]
#[tauri::command]
async fn check_for_update(_app: tauri::AppHandle) -> Result<UpdateStatus, String> {
    Err("signed updater is not enabled in this build".to_string())
}

#[cfg(feature = "signed-updater")]
#[tauri::command]
async fn install_update(
    app: tauri::AppHandle,
    pending_update: tauri::State<'_, PendingUpdate>,
    approved: bool,
    expected_version: String,
) -> Result<UpdateInstallStatus, String> {
    if !approved {
        return Err("installing an update requires explicit approved=true".to_string());
    }
    let expected_version = expected_version.trim();
    if expected_version.is_empty() {
        return Err("installing an update requires the explicitly checked version".to_string());
    }

    let update = {
        let mut pending = pending_update
            .0
            .lock()
            .map_err(|_| "pending updater state is unavailable".to_string())?;
        pending.take().ok_or_else(|| {
            "no checked update is pending; run an explicit update check first".to_string()
        })?
    };
    let version = update.version.to_string();
    if version != expected_version {
        return Err(
            "checked update no longer matches the operator-approved version; run the update check again"
                .to_string(),
        );
    }
    update
        .download_and_install(|_, _| {}, || {})
        .await
        .map_err(|error| error.to_string())?;
    let result = UpdateInstallStatus {
        installed: true,
        version: Some(version),
    };
    app.restart();
    Ok(result)
}

#[cfg(not(feature = "signed-updater"))]
#[tauri::command]
async fn install_update(
    _app: tauri::AppHandle,
    approved: bool,
    _expected_version: String,
) -> Result<UpdateInstallStatus, String> {
    if !approved {
        return Err("installing an update requires explicit approved=true".to_string());
    }
    Err("signed updater is not enabled in this build".to_string())
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
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init());
    #[cfg(feature = "signed-updater")]
    let builder = builder
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(PendingUpdate::default());

    builder
        .setup(|app| {
            #[cfg(feature = "updater-e2e")]
            updater_e2e::maybe_start(app.handle());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            runtime_probe,
            divan_capabilities,
            check_for_update,
            install_update,
            core_request
        ])
        .run(tauri::generate_context!())
        .expect("error while running Divan Desktop");
}
