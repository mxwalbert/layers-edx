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
git clone https://github.com/yourusername/layers-edx.git
cd layers-edx
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Set Up EPQ Library (for cross-validation tests)

**Option A: Automated Setup (Recommended - Windows)**
```powershell
.\scripts\setup_epq.ps1
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

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest

# Run only EPQ cross-validation tests
pytest -m epq

# Run specific test file
pytest test/test_xrt/test_xrt.py
```

## Project Structure

```
layers-edx/
├── .venv/                      # Virtual environment (not in git)
│   └── share/java/EPQ/         # EPQ Java library for testing
├── layers_edx/                 # Main Python package
│   ├── element.py
│   ├── xrt.py
│   └── ...
├── test/                       # Test suite
│   ├── conftest.py             # Pytest configuration
│   ├── test_xrt/               # X-ray transition tests
│   │   ├── test_xrt.py         # Python tests
│   │   └── test_xrt.java       # EPQ reference implementation
│   └── test_material_properties/
├── scripts/                    # Setup and utility scripts
│   └── setup_epq.ps1           # EPQ setup automation
├── pyproject.toml              # Python project configuration
└── README.md
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

**How it works:**
1. Compiles and runs Java test files (e.g., `test_xrt.java`)
2. Compares Java (EPQ) output with Python (layers-edx) output
3. Validates results match within tolerance

## Code Style

We follow PEP 8 for Python code. Consider using:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

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

## VSCode Setup (Optional)

The repository includes `.vscode/settings.json` (gitignored) which configures:
- Java classpath for EPQ library
- Python environment

After running the setup, VS Code should automatically recognize the Java classes.

## Questions?

If you encounter issues not covered here, please:
1. Check existing [Issues](https://github.com/yourusername/layers-edx/issues)
2. Open a new issue with details about your problem
3. Include your OS, Python version, and Java version

Thank you for contributing! 🎉
