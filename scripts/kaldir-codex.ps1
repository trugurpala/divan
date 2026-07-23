Write-Warning "scripts/kaldir-codex.ps1 is deprecated; use uninstall_codex.ps1"
& "$PSScriptRoot\uninstall_codex.ps1" @args
exit $LASTEXITCODE
