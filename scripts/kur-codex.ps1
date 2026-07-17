# Divan'i Codex icin kurar (Windows PowerShell)
# Kullanim: irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
$ErrorActionPreference = "Stop"
$src = Join-Path $env:TEMP "divan-kur"
if (Test-Path $src) { Remove-Item $src -Recurse -Force }
$zip = Join-Path $env:TEMP "divan.zip"
Invoke-WebRequest "https://github.com/trugurpala/divan/archive/refs/heads/main.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath $src -Force
$dst = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem "$src\divan-main\plugins\*\skills\*" -Directory | ForEach-Object {
  Copy-Item $_.FullName -Destination $dst -Recurse -Force
  Write-Host ("  vezir: " + $_.Name)
}
Remove-Item $zip -Force; Remove-Item $src -Recurse -Force
Write-Host ""
Write-Host "Divan kuruldu -> $dst"
Write-Host "Codex'i yeniden baslat, sonra dene: 'bastan sona yap: kucuk bir todo uygulamasi'"
