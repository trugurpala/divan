Write-Warning "scripts/kur-codex.ps1 is deprecated; use install_codex.ps1"
& "$PSScriptRoot\install_codex.ps1" @args
exit $LASTEXITCODE
