# Find Ollama logs wherever they actually are
$out = "$PSScriptRoot\ollama_diag"
New-Item -ItemType Directory -Force -Path $out | Out-Null

# Search common Ollama log locations on Windows
$candidates = @(
    "$env:LOCALAPPDATA\Ollama\logs",
    "$env:LOCALAPPDATA\Ollama",
    "$env:APPDATA\Ollama",
    "$env:LOCALAPPDATA\Programs\Ollama",
    "$env:USERPROFILE\.ollama",
    "C:\Users\Tom Beck\.ollama"
)

Write-Host "=== Searching for Ollama log directories ==="
foreach ($path in $candidates) {
    if (Test-Path $path) {
        Write-Host "FOUND: $path"
        Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '\.(log|txt)$' -or $_.Name -match 'log' } |
            Select-Object FullName, Length, LastWriteTime |
            Format-Table
    } else {
        Write-Host "NOT FOUND: $path"
    }
}

# Copy any log files found
Write-Host "`n=== Copying log files ==="
foreach ($path in $candidates) {
    if (Test-Path $path) {
        $logFiles = Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
            Where-Object { !$_.PSIsContainer -and ($_.Name -match '\.(log|txt)$' -or $_.Name -match 'log') }
        foreach ($f in $logFiles) {
            $dest = Join-Path $out ("ollama_" + $f.Name)
            Copy-Item $f.FullName $dest -Force
            Write-Host "Copied: $($f.FullName) -> $dest"
        }
    }
}

# Show Ollama install location and version details
Write-Host "`n=== Ollama executable location ==="
$ollExe = (Get-Command ollama -ErrorAction SilentlyContinue).Source
Write-Host "ollama.exe: $ollExe"
if ($ollExe) {
    $dir = Split-Path $ollExe
    Write-Host "Install dir contents:"
    Get-ChildItem $dir | Format-Table Name, Length, LastWriteTime
}

# Check OLLAMA_MODELS env var
Write-Host "`n=== Ollama environment ==="
[Environment]::GetEnvironmentVariables("User") | Where-Object { $_.Key -match "OLLAMA" } | Format-Table
[Environment]::GetEnvironmentVariables("Machine") | Where-Object { $_.Key -match "OLLAMA" } | Format-Table

# System RAM info
Write-Host "`n=== System RAM ==="
$cs = Get-CimInstance Win32_ComputerSystem
Write-Host "Total RAM: $([math]::Round($cs.TotalPhysicalMemory / 1GB, 1)) GB"

Write-Host "`nDone."
Read-Host "Press Enter to close"
