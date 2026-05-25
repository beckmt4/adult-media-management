# SSH into Unraid and set up git installation script for Stash
$SSHKey = "$env:USERPROFILE\.codex-ssh\claude_cowork_ed25519"
$UnraidHost = "root@192.168.1.147"

Write-Host "Creating git installation script on Unraid..." -ForegroundColor Green

# Create the install-git.sh script
$scriptContent = @"
#!/bin/sh
echo "Installing git..."
apk add --no-cache git
echo "Git installed successfully"
"@

# SSH to Unraid and create the file
ssh -i $SSHKey $UnraidHost @"
mkdir -p /mnt/container/appdata/stash
cat > /mnt/container/appdata/stash/install-git.sh << 'SCRIPT_EOF'
$scriptContent
SCRIPT_EOF
chmod +x /mnt/container/appdata/stash/install-git.sh
ls -la /mnt/container/appdata/stash/install-git.sh
echo "Script created successfully!"
"@

Write-Host "Done! The install-git.sh script is now on your Unraid server." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to Unraid WebUI > Docker"
Write-Host "2. Find your Stash container and click Edit"
Write-Host "3. Scroll to 'Extra Parameters'"
Write-Host "4. Add this line:"
Write-Host ""
Write-Host '   -v /mnt/container/appdata/stash/install-git.sh:/etc/cont-init.d/01-install-git:ro' -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Click Apply to restart the container"
Write-Host ""
Write-Host "That's it! Git will install automatically on every container start."
