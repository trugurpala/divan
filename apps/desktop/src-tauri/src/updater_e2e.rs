use std::{env, fs, path::PathBuf};

use tauri::{AppHandle, Manager};
use tauri_plugin_updater::UpdaterExt;

const MODE_ENV: &str = "DIVAN_UPDATER_E2E_MODE";
const EXPECTED_ENV: &str = "DIVAN_UPDATER_E2E_EXPECTED_VERSION";
const MARKER_ENV: &str = "DIVAN_UPDATER_E2E_MARKER";

pub fn maybe_start(app: &AppHandle) {
    let Ok(mode) = env::var(MODE_ENV) else {
        return;
    };
    if mode.trim().is_empty() {
        return;
    }

    let app = app.clone();
    tauri::async_runtime::spawn(async move {
        run(app, mode).await;
    });
}

async fn run(app: AppHandle, mode: String) {
    let expected = match env::var(EXPECTED_ENV) {
        Ok(value) if !value.trim().is_empty() => value.trim().to_string(),
        _ => {
            finish(
                &app,
                None,
                "fail",
                &mode,
                "unknown",
                "unknown",
                "expected version is missing",
                91,
            );
            return;
        }
    };
    let marker = env::var(MARKER_ENV).ok().map(PathBuf::from);
    let current = app.package_info().version.to_string();

    match mode.as_str() {
        "report-version" => {
            if current == expected {
                finish(
                    &app,
                    marker.as_ref(),
                    "pass",
                    &mode,
                    &current,
                    &expected,
                    "installed version matches expected version",
                    0,
                );
            } else {
                finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    "installed version does not match expected version",
                    92,
                );
            }
        }
        "install" => {
            if current == expected {
                finish(
                    &app,
                    marker.as_ref(),
                    "pass",
                    &mode,
                    &current,
                    &expected,
                    "updated application relaunched at expected version",
                    0,
                );
                return;
            }
            let updater = match app.updater() {
                Ok(value) => value,
                Err(error) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        &format!("updater initialization failed: {error}"),
                        93,
                    );
                    return;
                }
            };
            let update = match updater.check().await {
                Ok(Some(value)) => value,
                Ok(None) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        "expected update was not offered",
                        94,
                    );
                    return;
                }
                Err(error) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        &format!("update check failed: {error}"),
                        95,
                    );
                    return;
                }
            };
            if update.version.to_string() != expected {
                finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    "offered update version does not match expected version",
                    96,
                );
                return;
            }
            if let Err(error) = update.download_and_install(|_, _| {}, || {}).await {
                finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    &format!("signed update install failed: {error}"),
                    97,
                );
                return;
            }

            // On Windows the updater may terminate the current process while the
            // installer runs. If control returns, explicitly relaunch; the new
            // process sees current == expected and records the PASS marker.
            app.restart();
        }
        "expect-install-error" => {
            let updater = match app.updater() {
                Ok(value) => value,
                Err(error) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        &format!("updater initialization failed: {error}"),
                        98,
                    );
                    return;
                }
            };
            let update = match updater.check().await {
                Ok(Some(value)) => value,
                Ok(None) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        "tampered update metadata was not offered for signature test",
                        99,
                    );
                    return;
                }
                Err(error) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        &format!("update check failed before signature test: {error}"),
                        100,
                    );
                    return;
                }
            };
            if update.version.to_string() != expected {
                finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    "signature-test update version does not match expected version",
                    101,
                );
                return;
            }
            match update.download_and_install(|_, _| {}, || {}).await {
                Err(_) => finish(
                    &app,
                    marker.as_ref(),
                    "pass",
                    &mode,
                    &current,
                    &expected,
                    "tampered updater signature was rejected",
                    0,
                ),
                Ok(()) => finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    "tampered updater signature unexpectedly installed",
                    102,
                ),
            }
        }
        "expect-no-update" => {
            if current != expected {
                finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    "downgrade check is not running from the expected installed version",
                    103,
                );
                return;
            }
            let updater = match app.updater() {
                Ok(value) => value,
                Err(error) => {
                    finish(
                        &app,
                        marker.as_ref(),
                        "fail",
                        &mode,
                        &current,
                        &expected,
                        &format!("updater initialization failed: {error}"),
                        104,
                    );
                    return;
                }
            };
            match updater.check().await {
                Ok(None) => finish(
                    &app,
                    marker.as_ref(),
                    "pass",
                    &mode,
                    &current,
                    &expected,
                    "older signed release was not offered as a downgrade",
                    0,
                ),
                Ok(Some(update)) => finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    &format!("unexpected downgrade/update was offered: {}", update.version),
                    105,
                ),
                Err(error) => finish(
                    &app,
                    marker.as_ref(),
                    "fail",
                    &mode,
                    &current,
                    &expected,
                    &format!("downgrade check failed: {error}"),
                    106,
                ),
            }
        }
        _ => finish(
            &app,
            marker.as_ref(),
            "fail",
            &mode,
            &current,
            &expected,
            "unknown updater e2e mode",
            107,
        ),
    }
}

fn finish(
    app: &AppHandle,
    marker: Option<&PathBuf>,
    status: &str,
    mode: &str,
    current: &str,
    expected: &str,
    detail: &str,
    exit_code: i32,
) {
    if let Some(path) = marker {
        let detail = detail.replace(['\r', '\n'], " ");
        let body = format!(
            "status={status}\nmode={mode}\ncurrent={current}\nexpected={expected}\ndetail={detail}\n"
        );
        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let temporary = path.with_extension("tmp");
        if fs::write(&temporary, body).is_ok() {
            let _ = fs::remove_file(path);
            let _ = fs::rename(temporary, path);
        }
    }
    app.exit(exit_code);
}
