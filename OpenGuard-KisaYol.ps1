$Desktop = [Environment]::GetFolderPath("Desktop")
$Target  = Join-Path $Desktop "OpenGuard-Başlat.bat"
$ShortcutPath = Join-Path $Desktop "OpenGuard.lnk"

if (-not (Test-Path $Target)) {
    Write-Host "HATA: OpenGuard-Başlat.bat masaüstünde bulunamadı!" -ForegroundColor Red
    pause
    exit
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = $Desktop
$Shortcut.Description = "OpenGuard - Halka açık ağ sertleştirme aracı"
$Shortcut.IconLocation = "imageres.dll,1"
$Shortcut.Save()

Write-Host ""
Write-Host "  Masaüstüne 'OpenGuard' kısayolu oluşturuldu." -ForegroundColor Green
Write-Host ""
pause