# Copies Ollama logs + diagnostics to this folder for Claude to read
$out = "$PSScriptRoot\ollama_diag"
New-Item -ItemType Directory -Force -Path $out | Out-Null

# Ollama log files
$logDir = "$env:LOCALAPPDATA\Ollama\logs"
if (Test-Path $logDir) {
    Copy-Item "$logDir\*" $out -Recurse -Force
    Write-Host "Copied logs from $logDir"
} else {
    Write-Host "Log dir not found: $logDir"
}

# Ollama version
$ver = & ollama --version 2>&1
$ver | Out-File "$out\version.txt"

# GPU info
$gpu = & nvidia-smi 2>&1
$gpu | Out-File "$out\nvidia-smi.txt"

# Ollama model list
$models = & ollama list 2>&1
$models | Out-File "$out\models.txt"

# Windows Event Log - Application errors in last 24h
Get-WinEvent -LogName Application -MaxEvents 200 |
    Where-Object { $_.TimeCreated -gt (Get-Date).AddDays(-2) -and $_.LevelDisplayName -in 'Error','Warning' } |
    Select-Object TimeCreated, LevelDisplayName, ProviderName, Message |
    Format-List |
    Out-File "$out\eventlog_errors.txt"

# Ollama process info (if running)
Get-Process -Name "ollama*" -ErrorAction SilentlyContinue |
    Format-List | Out-File "$out\ollama_process.txt"

Write-Host "Done. Output in: $out"
Read-Host "Press Enter to close"
