# Generated Desktop resources

The Windows build generates two runtime artifacts from the exact checked-out Divan commit:

- `divan-runtime.exe` — production standalone runtime bundled into the installer. It does not require a system Python installation.
- `divan-project.pyz` — portable developer/fallback runtime used for independent contract verification.

Neither generated binary is committed to the repository.

For local development the Desktop backend accepts `DIVAN_RUNTIME_EXE` first and `DIVAN_PROJECT_PYZ` as the Python fallback.
