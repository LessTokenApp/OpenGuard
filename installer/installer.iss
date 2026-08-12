; OpenGuard Installer Setup Script (Inno Setup)
; This script creates an installer for the OpenGuard application
;
; Prerequisites:
; - PyInstaller executable built to: dist\OpenGuard\OpenGuard.exe
; - Inno Setup 6.0+ installed
; - OpenGuard.ps1 in the root directory

[Setup]
; Every path below is written relative to the repository root, not to this
; file, so point SourceDir there. Without it Inno resolves them against
; installer/ and the build fails on the first missing file.
SourceDir=..
AppName=OpenGuard
AppVersion=0.7.0
; NOTE: AppPublisher must match the Common Name (CN) on the code signing
; certificate exactly. Verify the exact string the CA issues before signing;
; changing it later resets SmartScreen reputation.
AppPublisher=Nuraydin Arikan
AppPublisherURL=https://github.com/LessTokenApp/OpenGuard
AppSupportURL=https://github.com/LessTokenApp/OpenGuard/issues
AppUpdatesURL=https://github.com/LessTokenApp/OpenGuard/releases
AppCopyright=Copyright (C) 2024-2026 Nuraydin Arikan
AppComments=Professional Python GUI application for Windows system hardening and security analysis
DefaultDirName={autopf}\OpenGuard
DefaultGroupName=OpenGuard
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=OpenGuard-Setup-0.7.0
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
LicenseFile=LICENSE
; Windows 11 is 10.0 build 22000, matching the documented minimum. Inno
; refuses the install with its own message, so no scripted check is needed.
MinVersion=10.0.22000
ChangesAssociations=no
WizardStyle=modern
UninstallDisplayIcon={app}\OpenGuard.exe
SetupIconFile=installer\openguard.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main PyInstaller executable and dependencies
Source: "dist\OpenGuard\OpenGuard.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\OpenGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; PowerShell backend script
Source: "OpenGuard.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

; Additional PowerShell scripts
Source: "OpenGuard-Hardening.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "Analytics-Dashboard.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "OpenGuard-Reminder.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "OpenGuard-KisaYol.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

; Documentation and license
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\OpenGuard"; Filename: "{app}\OpenGuard.exe"; IconIndex: 0; Comment: "OpenGuard Security Application"
Name: "{group}\{cm:UninstallProgram,OpenGuard}"; Filename: "{uninstallexe}"

; Desktop icon (optional, controlled by task). Uses the "auto" constant so an
; admin-mode install writes to the common desktop rather than the elevating
; account's own, which would hide the icon from the actual user.
Name: "{autodesktop}\OpenGuard"; Filename: "{app}\OpenGuard.exe"; IconIndex: 0; Comment: "OpenGuard Security Application"; Tasks: desktopicon

[Run]
; Launch the application after installation
Filename: "{app}\OpenGuard.exe"; Description: "{cm:LaunchProgram,OpenGuard}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional - can be commented out to preserve user settings)
; Type: filesandordirs; Name: "{localappdata}\OpenGuard"
Type: files; Name: "{app}\scripts\*"
Type: filesandordirs; Name: "{app}"

[InstallDelete]
; Remove old installations before installing new version
Type: files; Name: "{app}\OpenGuard.exe.old"

[Code]
{ Custom code for installation validation }

procedure InitializeWizard;
begin
  { Optional: Add any custom initialization code here }
  { For example: version checks, dependency validation, etc. }
end;

// Referenced by the [INI] section via a code: prefix to stamp the install
// date. Inno requires the String parameter even when it goes unused.
function GetCurrentDateTimeString(Param: String): String;
begin
  Result := GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Optional: Post-installation actions }
    { For example: registering file associations, creating config files, etc. }
    MsgBox('OpenGuard has been installed successfully. ' + #13#13 +
           'Please note: Administrator privileges are required to run hardening operations.',
           mbInformation, MB_OK);
  end;
end;

[INI]
; Optional: Store installation preferences
Filename: "{app}\OpenGuard.ini"; Section: "Installation"; Key: "InstalledDate"; String: "{code:GetCurrentDateTimeString}"
Filename: "{app}\OpenGuard.ini"; Section: "Installation"; Key: "Version"; String: "0.7.0"

[Registry]
; Add program to Add/Remove Programs (handled automatically by Inno Setup)
; Add application path registry for scripts
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenGuard"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"; Flags: deletevalue
Root: HKLM; Subkey: "Software\OpenGuard"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\OpenGuard"; ValueType: string; ValueName: "Version"; ValueData: "0.7.0"
