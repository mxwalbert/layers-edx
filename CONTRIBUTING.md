# Contributing to layers-edx

Thank you for your interest in contributing to layers-edx! This guide will help you set up your development environment.

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Java Development Kit (JDK) 21+** (for EPQ cross-validation tests)
   - Download from [Adoptium](https://adoptium.net/)
   - Verify: `java -version`
   - **Why?** We validate our Python implementation against the NIST EPQ Java library

3. **Apache Maven 3.6+** (for building EPQ)
   - Download from [maven.apache.org](https://maven.apache.org/download.cgi)
   - Verify: `mvn -version`

4. **Git**
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mxwalbert/layers-edx.git
cd layers-edx
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# - Windows (PowerShell):
.venv\Scripts\Activate.ps1
# - Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Set Up EPQ Library (for cross-validation tests)

**Option A: Automated Setup (Recommended)**
```bash
# - Windows (PowerShell):
.\scripts\setup_epq.ps1
# - Linux/Mac:
./scripts/setup_epq.sh
```

**Option B: Manual Setup**
```bash
# Create directory for Java libraries
mkdir -p .venv/share/java
cd .venv/share/java

# Clone EPQ repository
git clone https://github.com/usnistgov/EPQ.git
cd EPQ

# Compile EPQ
mvn compile

# Copy Maven dependencies (required for tests)
mvn dependency:copy-dependencies -DoutputDirectory=target/dependency

# Return to project root
cd ../../../..
```

### 4. Verify Setup

Run verification test to check if the EPQ environment is properly configured:

```bash
pytest -m epq_env -v
```

## Running Tests

### Python Unit Tests
```bash
# Run all unit tests
pytest

# Run with coverage
pytest --cov=layers_edx

# Run specific test file
pytest test/test_xrt/test_xrt.py -v
```

### EPQ Cross-Validation Tests

These tests validate the Python implementation against the NIST EPQ Java library:

```bash
# Run all EPQ validation tests
pytest -m epq

# Run specific EPQ test
pytest test/test_xrt/test_xrt.py::test_xrt_silicon_k_vs_epq -v
```

**Test Markers:**
- `@pytest.mark.epq` - EPQ cross-validation tests
- `@pytest.mark.epq_env` - EPQ environment setup tests

**How it works:**
1. Compiles and runs Java test files (e.g., `test_xrt.java`)
2. Compares Java (EPQ) output with Python (layers-edx) output
3. Validates results match within tolerance

## Code Style

We follow PEP 8 for Python code with one exception: we use a line length limit of **88 characters** (instead of the PEP8 default of 79). This choice, following [SciPy's rationale](https://docs.scipy.org/doc/scipy/dev/contributor/pep8.html), strikes a balance between producing shorter files, reducing linter errors, maintaining reasonably short lines, and enabling side-by-side file viewing.

We use **[ruff](https://github.com/astral-sh/ruff)** as our unified linter and code formatter.

### Running Code Quality Tools

```bash
# Format code
ruff format

# Check code for linting issues
ruff check

# Auto-fix fixable issues
ruff check --fix
```

Ruff is configured in `pyproject.toml`

## Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Run the test suite to ensure nothing breaks:
   ```bash
   pytest
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork and submit a pull request

## Troubleshooting

### EPQ Tests Fail with "EPQ classes not found"

Run the EPQ setup script:
```powershell
.\scripts\setup_epq.ps1
```

### Java Compilation Errors

Ensure you have Java 21+ installed:
```bash
java -version
```

### Maven Errors

Ensure Maven is properly installed and in your PATH:
```bash
mvn -version
```

### Import Errors

Make sure you've installed the package in development mode:
```bash
pip install -e ".[dev]"
```

## Need support?

If you encounter problems setting up the environment, please open an [issue](https://github.com/mxwalbert/layers-edx/issues) (check existing issues first!).

Thank you for contributing! 🎉
