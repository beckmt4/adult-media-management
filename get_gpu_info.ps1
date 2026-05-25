# GPU Specs script
$gpu = Get-WmiObject -Class Win32_VideoController | Where-Object {$_.Name -like "*NVIDIA*"} | Select-Object Name, AdapterRAM, DriverVersion, VideoModeDescription
$gpu | ForEach-Object {
    $vramGB = [math]::Round($_.AdapterRAM / 1GB, 1)
    "GPU: $($_.Name) | VRAM: ${vramGB} GB | Driver: $($_.DriverVersion)"
}
$cpu = Get-WmiObject -Class Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed
$cpu | ForEach-Object {
    "CPU: $($_.Name) | Cores: $($_.NumberOfCores) | Threads: $($_.NumberOfLogicalProcessors) | MaxMHz: $($_.MaxClockSpeed)"
}
$ram = Get-WmiObject -Class Win32_ComputerSystem | Select-Object TotalPhysicalMemory
"RAM: $([math]::Round($ram.TotalPhysicalMemory / 1GB, 0)) GB"
$os = Get-WmiObject -Class Win32_OperatingSystem | Select-Object Caption, Version
"OS: $($os.Caption) $($os.Version)"
$result | Out-File "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\workstation_specs.txt" -Encoding UTF8
