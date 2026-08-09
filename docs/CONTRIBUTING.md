# Contributing to OpenGuard

Thank you for your interest in contributing to OpenGuard! This guide will help you set up your development environment, run tests, and follow our Git workflow.

---

## Development Setup

### Prerequisites
- **Windows 11 Pro/Enterprise** (development platform)
- **Python 3.12+** ([python.org](https://www.python.org))
- **Git** ([git-scm.com](https://git-scm.com))
- **PowerShell 5.1+** (included with Windows)
- **Administrator access** (for testing hardening features)

### Step 1: Clone the Repository

```bash
git clone https://github.com/openguard/openguard.git
cd OpenGuard
```

### Step 2: Create Virtual Environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Or Windows CMD
python -m venv venv
venv\Scripts\activate.bat

# Or Git Bash
python -m venv venv
source venv/Scripts/activate
```

### Step 3: Install Dependencies

```bash
# Install core + dev dependencies
pip install -e ".[dev,test]"
```

This installs:
- PyQt6 (6.6.0+) - GUI framework
- PyYAML (6.0+) - Configuration management
- pytest (7.4.0+) - Testing framework
- pytest-qt (4.2.0+) - Qt testing utilities
- pytest-cov (4.1.0+) - Coverage reporting
- black - Code formatter
- ruff - Linter
- mypy - Type checker
- isort - Import sorter

### Step 4: Verify Installation

```bash
# Run a quick test to verify setup
pytest --version
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

---

## Project Structure Reference

```
src/
├── main.py                 # Entry point
├── app.py                  # Application class
├── core/                   # Business logic
│   ├── hardening_manager.py
│   ├── analytics_engine.py
│   ├── config_manager.py
│   └── process_monitor.py
├── models/                 # Data models
│   ├── event.py
│   └── settings.py
└── ui/                     # UI components
    ├── main_window.py
    ├── settings_dialog.py
    ├── analytics_modal.py
    ├── onboarding_wizard.py
    └── styles.py

tests/
├── test_*.py              # Unit/integration tests
└── *_test.py

docs/
├── ARCHITECTURE.md        # Architecture guide
├── CONTRIBUTING.md        # This file
└── README.md             # User guide
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# UI tests (requires display)
pytest -m ui

# Single test file
pytest tests/test_config_manager.py

# Single test function
pytest tests/test_config_manager.py::test_load_config_creates_defaults
```

### Test Output Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show last 10 failures
pytest --lf -v

# Show test durations
pytest --durations=10
```

---

## Code Quality Checks

### Formatting (Black)

```bash
# Format all Python files
black src/ tests/

# Check without changing
black --check src/ tests/
```

### Linting (Ruff)

```bash
# Check code style
ruff check src/ tests/

# Auto-fix simple issues
ruff check --fix src/ tests/
```

### Type Checking (Mypy)

```bash
# Type check the codebase
mypy src/

# Ignore missing imports (already configured)
mypy src/ --ignore-missing-imports
```

### Import Sorting (Isort)

```bash
# Sort imports
isort src/ tests/

# Check without changing
isort --check-only src/ tests/
```

### Run All Quality Checks

```bash
# Format and lint
black src/ tests/ && ruff check --fix src/ tests/

# Check types
mypy src/

# Sort imports
isort src/ tests/

# Run tests
pytest
```

---

## Development Workflow

### Branch Naming

Follow these naming conventions for branches:

- **Feature:** `feature/description` (e.g., `feature/add-analytics-modal`)
- **Bug Fix:** `fix/description` (e.g., `fix/ps1-timeout-issue`)
- **Refactor:** `refactor/description` (e.g., `refactor/hardening-manager`)
- **Docs:** `docs/description` (e.g., `docs/api-guide`)
- **Task:** `task/number-description` (e.g., `task/15-documentation`)

### Git Workflow

#### 1. Create a Branch

```bash
# Make sure you're on main/master
git checkout master

# Pull latest changes
git pull origin master

# Create your branch
git checkout -b feature/my-feature
```

#### 2. Make Changes

- Write code following the project style
- Add tests for new functionality
- Update documentation if needed
- Keep commits focused and logical

#### 3. Commit Changes

```bash
# Stage files
git add src/my_module.py tests/test_my_module.py

# Commit with descriptive message
git commit -m "feat: add feature description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `docs:` Documentation update
- `test:` Test addition/modification
- `chore:` Build, dependencies, etc.

**Example Messages:**
```
feat: implement analytics modal with FREE/PRO tiers
fix: resolve PowerShell timeout on slow systems
docs: add CONTRIBUTING.md with dev setup guide
test: add unit tests for config_manager
```

#### 4. Keep Your Branch Updated

```bash
# Before creating PR
git fetch origin
git rebase origin/master
```

#### 5. Push to Remote

```bash
git push origin feature/my-feature
```

#### 6. Create Pull Request

1. Go to GitHub: `github.com/openguard/openguard`
2. Click "New Pull Request"
3. Select your branch
4. Fill in PR description:
   - Summary of changes
   - Related issues
   - Screenshots (if UI changes)
   - Testing instructions

#### 7. Address Review Feedback

```bash
# Make requested changes
# ... edit files ...

# Commit changes
git add .
git commit -m "fix: address review feedback"

# Push to update PR
git push origin feature/my-feature
```

#### 8. Merge to Main

After approval:
- Use "Squash and merge" for single-feature branches
- Use "Create merge commit" for multi-commit work
- Delete remote branch after merging

---

## Common Development Tasks

### Adding a New Feature

1. Create branch: `git checkout -b feature/my-feature`
2. Create module in appropriate `src/` subdirectory
3. Add unit tests in `tests/`
4. Update `docs/` if API changes
5. Run tests: `pytest`
6. Run quality checks: `black src/ && ruff check --fix src/ && mypy src/`
7. Commit and push
8. Create PR

### Running the Application

```bash
# From project root
python -m src.main

# Or using entry point
python src/main.py
```

### Debugging with Print Statements

```bash
# Run tests with output
pytest -s

# Print statements in test will be visible
```

### Using Type Hints

Always add type hints to function signatures:

```python
def calculate_risk_score(events: List[Event]) -> float:
    """Calculate risk score from events.
    
    Args:
        events: List of security events
        
    Returns:
        Risk score between 0 and 1
    """
    ...
```

### Writing Tests

```python
import pytest
from src.models.event import Event

@pytest.mark.unit
def test_event_validation():
    """Test that Event validates severity levels."""
    with pytest.raises(ValueError):
        Event(
            timestamp=datetime.now(),
            event="Test",
            severity="INVALID"
        )
```

### Handling Errors

```bash
# Clear pytest cache if tests act weird
rm -r .pytest_cache __pycache__

# Reinstall packages
pip install -e ".[dev,test]" --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## PowerShell Development

### Testing PowerShell Backend

The PowerShell script (`backend/OpenGuard.ps1`) requires:
- Administrator privileges
- Windows Registry access
- Windows Firewall access

### Local Testing (Requires Admin)

```powershell
# PowerShell as Administrator
cd OpenGuard
.\backend\OpenGuard.ps1 -Action Enable -Level Moderate

# Check status
# (Implementation-specific)

# Disable
.\backend\OpenGuard.ps1 -Action Disable
```

---

## Documentation

### Writing Documentation

- Use Markdown format
- Add code examples
- Include diagrams for complex flows
- Link to related documentation
- Update TABLE OF CONTENTS if adding new sections

### Documentation Files

- `README.md` - User-facing introduction
- `docs/ARCHITECTURE.md` - Developer architecture guide
- `docs/CONTRIBUTING.md` - This file
- Inline code comments - Docstrings for classes/functions

### Example Docstring

```python
def enable_hardening(self, level: str = "Moderate") -> bool:
    """Call PowerShell to enable hardening.

    Args:
        level: Hardening level (e.g., "Low", "Moderate", "High").
               Defaults to "Moderate".

    Returns:
        bool: True if hardening was enabled successfully, False otherwise.
        
    Raises:
        subprocess.TimeoutExpired: If process takes >30 seconds.
    """
```

---

## Release Process

1. Update version in `pyproject.toml`
2. Update `README.md` with new features
3. Create annotated git tag: `git tag -a v0.7.0 -m "Release v0.7.0"`
4. Push tags: `git push origin --tags`
5. Create GitHub Release with changelog

---

## Getting Help

- **Issues:** Check [GitHub Issues](https://github.com/openguard/openguard/issues)
- **Discussions:** [GitHub Discussions](https://github.com/openguard/openguard/discussions)
- **Email:** info@openguard.app

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Follow the existing code style
- Test your changes thoroughly
- Document your work

---

## Additional Resources

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [pytest Documentation](https://docs.pytest.org/)
- [Git Workflow Guide](https://git-scm.com/book/en/v2)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

---

**Happy contributing!** 🚀
