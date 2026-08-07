use std::{env, fs, path::PathBuf};

fn updater_e2e_compile_placeholder() {
    if env::var_os("CARGO_FEATURE_UPDATER_E2E").is_none() {
        return;
    }

    let Some(target) = env::var_os("TARGET") else {
        return;
    };
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let binaries = manifest.join("binaries");
    let extension = if target.to_string_lossy().contains("windows") {
        ".exe"
    } else {
        ""
    };
    let sidecar = binaries.join(format!(
        "divan-core-{}{}",
        target.to_string_lossy(),
        extension
    ));
    if sidecar.exists() {
        return;
    }

    fs::create_dir_all(&binaries).expect("create updater e2e sidecar directory");
    fs::write(&sidecar, []).expect("create updater e2e compile placeholder");
    println!(
        "cargo:warning=created test-only updater-e2e externalBin compile placeholder at {}",
        sidecar.display()
    );
}

fn main() {
    updater_e2e_compile_placeholder();
    tauri_build::build()
}
