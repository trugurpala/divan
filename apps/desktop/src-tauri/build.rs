use std::{env, fs, path::PathBuf};

fn updater_e2e_compile_placeholders() {
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
    if !sidecar.exists() {
        fs::create_dir_all(&binaries).expect("create updater e2e sidecar directory");
        fs::write(&sidecar, []).expect("create updater e2e compile placeholder");
        println!(
            "cargo:warning=created test-only updater-e2e externalBin compile placeholder at {}",
            sidecar.display()
        );
    }

    let desktop_root = manifest
        .parent()
        .expect("Tauri manifest must live below the Desktop root");
    let dist = desktop_root.join("dist");
    let index = dist.join("index.html");
    if !index.exists() {
        fs::create_dir_all(&dist).expect("create updater e2e frontend dist directory");
        fs::write(
            &index,
            "<!doctype html><html><body>updater-e2e compile placeholder</body></html>\n",
        )
        .expect("create updater e2e frontend compile placeholder");
        println!(
            "cargo:warning=created test-only updater-e2e frontend compile placeholder at {}",
            index.display()
        );
    }
}

fn main() {
    updater_e2e_compile_placeholders();
    tauri_build::build()
}
