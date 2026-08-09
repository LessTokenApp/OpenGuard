; OpenGuard Installer Setup Script (Inno Setup)
; This script creates an installer for the OpenGuard application
;
; Prerequisites:
; - PyInstaller executable built to: dist\OpenGuard\OpenGuard.exe
; - Inno Setup 6.0+ installed
; - OpenGuard.ps1 in the root directory

[Setup]
AppName=OpenGuard
AppVersion=0.7.0
AppPublisher=OpenGuard Team
AppPublisherURL=https://github.com/NuraydinArikan/OpenGuard
AppSupportURL=https://github.com/NuraydinArikan/OpenGuard/issues
AppUpdatesURL=https://github.com/NuraydinArikan/OpenGuard/releases
AppCopyright=Copyright (C) 2024 OpenGuard Team
AppComments=Professional Python GUI application for Windows system hardening and security analysis
DefaultDirName={pf}\OpenGuard
DefaultGroupName=OpenGuard
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=OpenGuard-Setup-0.7.0
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
PrivilegesRequiredOverride=none
LicenseFile=LICENSE
ChangesAssociations=no
WizardStyle=modern
WizardResizable=yes
UninstallDisplayIcon={app}\OpenGuard.exe
SetupIconFile=installer\openguard.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1,10.0

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

; Desktop icon (optional, controlled by task)
Name: "{userdesktop}\OpenGuard"; Filename: "{app}\OpenGuard.exe"; IconIndex: 0; Comment: "OpenGuard Security Application"; Tasks: desktopicon

; Quick Launch icon (optional, only for older Windows versions)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\OpenGuard"; Filename: "{app}\OpenGuard.exe"; Comment: "OpenGuard Security Application"; Tasks: quicklaunchicon

[Run]
; Launch the application after installation
Filename: "{app}\OpenGuard.exe"; Description: "{cm:LaunchProgram,OpenGuard}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional - can be commented out to preserve user settings)
; Type: filesandordirs; Name: "{localappdata}\OpenGuard"
Type: files; Name: "{app}\scripts\*"
Type: dirsandfiles; Name: "{app}"

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

function InitializeSetup: Boolean;
begin
  Result := True;

  { Check if running on Windows (should always be true for this installer) }
  if not IsWin32 and not IsWin64 then
  begin
    MsgBox('This application requires Windows XP or later.', mbInformation, MB_OK);
    Result := False;
  end;

  { Optional: Check for Python runtime or other dependencies }
  { This can be added if runtime dependencies need to be verified }
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
