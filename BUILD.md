# OpenGuard Build Instructions

This document provides comprehensive instructions for building the OpenGuard application from source and creating an installer.

## System Requirements

- **Windows 11 Pro or Enterprise** (Windows 10 21H2 or later may work)
- **PowerShell 5.1 or later**
- **Python 3.12 or later**
- **pip** (Python package manager)
- **Inno Setup 6.0 or later** (for creating the installer)

## Build Process

### 1. Set Up Development Environment

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/LessTokenApp/OpenGuard.git
cd OpenGuard
```

Create a Python virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install PyInstaller
```

If `requirements.txt` doesn't exist, install the project in development mode:

```bash
pip install -e ".[dev]"
pip install PyInstaller
```

### 2. Build Executable with PyInstaller

Run the following PyInstaller command to create a standalone executable:

```bash
PyInstaller --name=OpenGuard ^
  --onedir ^
  --windowed ^
  --icon=installer/openguard.ico ^
  --add-data="src:src" ^
  --hidden-import=PyQt6.QtCore ^
  --hidden-import=PyQt6.QtGui ^
  --hidden-import=PyQt6.QtWidgets ^
  --distpath=dist ^
  --buildpath=build ^
  --specpath=build ^
  src/main.py
```

#### PyInstaller Command Breakdown

- `--name=OpenGuard`: Name of the generated executable
- `--onedir`: Create a directory with executable and dependencies (recommended)
- `--windowed`: No console window (GUI application)
- `--icon`: Application icon file path
- `--add-data`: Include data files (application resources)
- `--hidden-import`: Explicitly include PyQt6 modules that may be missed by analysis
- `--distpath=dist`: Output directory for the executable
- `--buildpath=build`: Temporary build directory
- `--specpath=build`: Location for the .spec file
- `src/main.py`: Entry point file

### 3. Verify Executable

Test the generated executable to ensure it runs correctly:

```bash
dist\OpenGuard\OpenGuard.exe
```

Expected behavior:
- Application window launches with GUI
- No console window appears
- All UI components render correctly
- Application can be closed normally

### 4. Create Installer with Inno Setup

#### 4.1 Install Inno Setup

Download and install **Inno Setup 6.0** or later from:
https://jrsoftware.org/isdl.php

#### 4.2 Prepare Icon File (Optional)

Create or place an application icon at:
`installer/openguard.ico`

If no icon is available, remove or comment out the `SetupIconFile` line in `installer/installer.iss`.

#### 4.3 Compile the Installer

**Using Inno Setup GUI:**

1. Open Inno Setup
2. Click **File > Open**
3. Navigate to and select `installer/installer.iss`
4. Click **Build > Compile**
5. The installer will be created at `dist/installer/OpenGuard-Setup-0.7.0.exe`

**Using Command Line:**

```bash
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer/installer.iss
```

### 5. Output Artifacts

After successful build, the following files are generated:

```
dist/
├── OpenGuard/                           # PyInstaller executable directory
│   ├── OpenGuard.exe                    # Main application executable
│   ├── PyQt6/                           # PyQt6 libraries
│   ├── _internal/                       # Python runtime and dependencies
│   └── scripts/                         # PowerShell scripts
│
└── installer/
    └── OpenGuard-Setup-0.7.0.exe        # Installer executable
```

## Installation

Users can now install OpenGuard by running:

```bash
dist/installer/OpenGuard-Setup-0.7.0.exe
```

### Installation Details

The installer will:

1. **Request Administrator Privileges**: Required for system hardening operations
2. **Create Installation Directory**: `C:\Program Files\OpenGuard`
3. **Install Application Files**:
   - Main executable and PyQt6/Python runtime
   - PowerShell backend scripts in `scripts/` subdirectory
   - README and LICENSE files
4. **Create Start Menu Shortcuts**: 
   - `Start Menu > OpenGuard > OpenGuard`
   - `Start Menu > OpenGuard > Uninstall OpenGuard`
5. **Optional Desktop Shortcut**: User can choose during installation
6. **Register with Windows**: Add/Remove Programs registry entries

### Uninstallation

Users can uninstall OpenGuard via:
- **Control Panel > Programs > Programs and Features** (recommended)
- **Start Menu > OpenGuard > Uninstall OpenGuard**
- **Add/Remove Programs** in Windows Settings

## Troubleshooting

### PyInstaller Issues

**Issue**: `ModuleNotFoundError` when running executable

**Solution**: Add the missing module to `--hidden-import` flag:
```bash
PyInstaller ... --hidden-import=missing_module ...
```

**Issue**: Missing DLLs or libraries

**Solution**: Manually copy dependencies to the `dist/OpenGuard/_internal/` directory or use `--collect-all` flag:
```bash
PyInstaller ... --collect-all=pyqt6 ...
```

### Inno Setup Issues

**Issue**: Icon file not found during compilation

**Solution**: Ensure `installer/openguard.ico` exists or comment out `SetupIconFile` in the .iss file

**Issue**: "Access denied" during installation

**Solution**: Run installer as Administrator or check file permissions in `dist/OpenGuard/`

### Runtime Issues

**Issue**: "The application has failed to start because no Python runtime was found"

**Solution**: This indicates PyInstaller didn't bundle Python correctly. Rebuild with `--onefile` or use `--collect-all` for all dependencies

**Issue**: PyQt6 modules not loading in installed application

**Solution**: Ensure all PyQt6 modules are included in the hidden imports and that the `_internal/` directory structure is preserved

## Clean Build

To perform a clean build (remove all previous build artifacts):

```bash
# Remove build directories
Remove-Item -Recurse -Force build
Remove-Item -Recurse -Force dist
Remove-Item -Path *.spec -ErrorAction SilentlyContinue

# Remove Python cache
Remove-Item -Recurse -Force src/__pycache__
Remove-Item -Recurse -Force src/*/__pycache__
```

Then follow the build process from step 2 onwards.

## Customization

### Changing Application Version

Update the version in three locations:

1. **pyproject.toml**: `version = "0.7.0"`
2. **installer.iss**: `AppVersion=0.7.0` and `OutputBaseFilename=OpenGuard-Setup-0.7.0`
3. **OpenGuard.ps1**: `$Version = "0.7.0"`

### Custom Installation Directory

Modify in `installer.iss`:
```ini
DefaultDirName={pf}\CustomAppName
```

### Custom Start Menu Folder

Modify in `installer.iss`:
```ini
DefaultGroupName=Custom Menu Folder
```

## Continuous Integration

For automated builds, use the following command sequence in CI/CD pipelines:

```bash
# Set up environment
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
pip install PyInstaller

# Build executable
PyInstaller --name=OpenGuard --onedir --windowed --icon=installer/openguard.ico --add-data="src:src" --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --distpath=dist --buildpath=build --specpath=build src/main.py

# Create installer (requires Inno Setup installed)
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer/installer.iss
```

## Support

For issues or questions about building OpenGuard:

- **GitHub Issues**: https://github.com/LessTokenApp/OpenGuard/issues
- **Email**: info@lesstoken.app
- **Documentation**: https://docs.openguard.app
