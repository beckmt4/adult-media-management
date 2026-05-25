$key1 = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\unraid_codex_ed25519"
$key2 = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\unraid_ed25519"
$host_ip = "root@192.168.1.147"
$out = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\audit_result.txt"

# Pick working key
$key = $key1
if (-not (Test-Path $key)) { $key = $key2 }

$ssh_opts = @("-i", $key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "ConnectTimeout=15", "-o", "IdentitiesOnly=yes")

function Run-SSH {
    param([string]$cmd)
    $result = & ssh @ssh_opts $host_ip $cmd 2>&1
    return $result -join "`n"
}

$report = @()
$report += "=== AUDIT: $(Get-Date) ==="
$report += ""

$report += "### DOCKER PS (all containers) ###"
$report += Run-SSH "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
$report += ""

$report += "### STASH config.yml FULL ###"
$report += Run-SSH "cat /mnt/user/appdata/stash/config.yml 2>/dev/null"
$report += ""

$report += "### WHISPARR config.xml ###"
$report += Run-SSH "cat /mnt/user/appdata/whisparr/config.xml 2>/dev/null || docker exec whisparr cat /config/config.xml 2>/dev/null || echo 'not found'"
$report += ""

$report += "### APPDATA DIRS ###"
$report += Run-SSH "ls /mnt/user/appdata/ 2>/dev/null"
$report += ""

$report += "### STASH PLUGINS ###"
$report += Run-SSH "ls -la /mnt/user/appdata/stash/plugins/ 2>/dev/null"
$report += ""

$report += "### STASH SCRAPERS ###"
$report += Run-SSH "ls -la /mnt/user/appdata/stash/scrapers/ 2>/dev/null"
$report += ""

$report += "### actress_library.yml ###"
$report += Run-SSH "cat /mnt/user/appdata/stash/plugins/actress_library/actress_library.yml 2>/dev/null || echo 'not found'"
$report += ""

$report += "### config.ini (redacted) ###"
$report += Run-SSH "cat /mnt/user/appdata/stash/stash-plugins/config.ini 2>/dev/null | sed 's/\(=\s*\).*/\1[REDACTED]/' || echo 'not found'"
$report += ""

$report += "### WHISPARR INSPECT ###"
$report += Run-SSH "docker inspect whisparr 2>/dev/null | python3 -c ""import json,sys; d=json.load(sys.stdin)[0]; print('Image:', d['Config']['Image']); print('Status:', d['State']['Status']); print('Mounts:', [(m['Source'], m['Destination']) for m in d['Mounts']])"" || echo 'not found'"
$report += ""

$report += "### ALL *ARR + MEDIA CONTAINERS ###"
$report += Run-SSH "docker ps -a --format '{{.Names}}|{{.Status}}|{{.Image}}' | grep -iE 'arr|plex|jellyfin|emby|prowlarr|stash|tautulli|overseerr|requestrr|notifiarr|flaresolverr'"
$report += ""

$report += "### STASH CONTAINER IMAGE ###"
$report += Run-SSH "docker inspect stash --format '{{.Config.Image}}|{{.State.Status}}|{{.State.StartedAt}}' 2>/dev/null"
$report += ""

$report += "### STASH PYTHON PACKAGES ###"
$report += Run-SSH "docker exec stash /config/py/venv/bin/pip list 2>/dev/null || echo 'no venv'"
$report += ""

$report += "### STASH CONTAINER ENV (filtered) ###"
$report += Run-SSH "docker exec stash env 2>/dev/null | grep -v 'KEY\|SECRET\|PASS\|TOKEN' | sort"
$report += ""

$report | Out-File -FilePath $out -Encoding utf8
Write-Host "Done -> $out"
