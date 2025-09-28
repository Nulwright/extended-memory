powershell# ESM Windows Desktop Integration

Write-Host "Setting up ESM desktop integration for Windows..." -ForegroundColor Green

# Get current directory
$ESMDir = Get-Location

# Set ESM API URLs in environment
[Environment]::SetEnvironmentVariable("OPENAI_API_BASE", "http://localhost:8001/v1", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_BASE", "http://localhost:8001/v1", "User")
[Environment]::SetEnvironmentVariable("ESM_DIR", $ESMDir, "User")

# Create desktop shortcut to ESM
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\ESM Dashboard.lnk")
$Shortcut.TargetPath = "http://localhost:3000"
$Shortcut.Description = "Extended Sienna Memory Dashboard"
$Shortcut.Save()

# Create startup script
$StartupScript = @"
# ESM Auto-Start Script
Set-Location "$ESMDir"
Start-Process "docker-compose" -ArgumentList "up -d" -WindowStyle Hidden
"@

$StartupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start-esm.ps1"
$StartupScript | Out-File -FilePath $StartupPath

# Create system tray notification
$ToastParams = @{
    Text = "ESM Windows integration complete! Your AI API calls will now be automatically captured."
    AppId = "ESM"
}

Write-Host "✅ Windows integration complete!" -ForegroundColor Green
Write-Host "🔄 Please restart your applications for API redirection to take effect" -ForegroundColor Yellow
Write-Host "🌐 ESM Dashboard shortcut created on desktop" -ForegroundColor Green
Write-Host "🚀 ESM will auto-start with Windows" -ForegroundColor Green