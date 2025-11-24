# Development Environment Setup Checklist

Use this checklist when setting up a new development environment for layers-edx.

## ✓ Prerequisites

- [ ] **Python 3.8+** installed
  ```bash
  python --version
  ```
  
- [ ] **Java 21+** installed (for EPQ cross-validation)
  ```bash
  java -version
  ```

- [ ] **Apache Maven 3.6+** installed (for EPQ compilation)
  ```bash
  mvn -version
  ```

- [ ] **Git** installed
  ```bash
  git --version
  ```

## ✓ Python Environment

- [ ] Clone repository
  ```bash
  git clone https://github.com/yourusername/layers-edx.git
  cd layers-edx
  ```

- [ ] Create virtual environment
  ```bash
  python -m venv .venv
  ```

- [ ] Activate virtual environment
  ```powershell
  # Windows PowerShell
  .venv\Scripts\Activate.ps1
  ```

- [ ] Install package in development mode
  ```bash
  pip install -e ".[dev]"
  ```

## ✓ EPQ Setup (Required for Cross-Validation Tests)

### Option A: Automated (Recommended)

- [ ] Run setup script
  ```powershell
  .\scripts\setup_epq.ps1
  ```

### Option B: Manual

- [ ] Create EPQ directory
  ```bash
  mkdir -p .venv/share/java
  cd .venv/share/java
  ```

- [ ] Clone EPQ repository
  ```bash
  git clone https://github.com/usnistgov/EPQ.git
  cd EPQ
  ```

- [ ] Compile EPQ
  ```bash
  mvn compile
  ```

- [ ] Copy Maven dependencies
  ```bash
  mvn dependency:copy-dependencies -DoutputDirectory=target/dependency
  ```

- [ ] Return to project root
  ```bash
  cd ../../../..
  ```

## ✓ Verification

- [ ] Run Python tests
  ```bash
  pytest
  ```

- [ ] Run EPQ cross-validation tests
  ```bash
  pytest -m epq
  ```

- [ ] Check specific test files
  ```bash
  pytest test/test_xrt/test_xrt.py -v
  ```

## ✓ VS Code Setup (Optional)

- [ ] Open project in VS Code
- [ ] Select Python interpreter from `.venv`
- [ ] Verify Java language server recognizes EPQ classes (no red squiggles in `.java` files)

## Troubleshooting

If tests fail:

1. **"EPQ classes not found"**
   - Run `.\scripts\setup_epq.ps1`
   - Verify `.venv/share/java/EPQ/target/classes` exists

2. **"NoClassDefFoundError: Jama/Matrix"**
   - Run `mvn dependency:copy-dependencies -DoutputDirectory=target/dependency` in EPQ directory
   - Verify `.venv/share/java/EPQ/target/dependency/*.jar` files exist

3. **Java version issues**
   - Ensure Java 21+ is installed
   - Check `java -version`

4. **Python import errors**
   - Verify virtual environment is activated
   - Run `pip install -e ".[dev]"` again

---

**Setup Complete!** 🎉

You're ready to contribute. See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.
