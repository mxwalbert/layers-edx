# Cross-Language Testing Strategy (Java → Python Port)

This project is a **full Python port** of the Java library [Electron Probe Quantification (EPQ)](https://github.com/usnistgov/EPQ) by NIST.

To ensure correctness, the Python implementation is continuously tested against the original Java behavior using a **reference dump strategy** (Golden Testing). The Java code is treated as an **oracle**, and Python tests verify that the ported implementation produces equivalent observable results.

## Overview

### How it works

- The original Java library is included as a **git submodule**
- The Java code is **not modified** but compiled and installed via Maven
- A small **CLI program** called *TestDump* provides an interface to instantiate Java classes
- *TestDump* emits **deterministic reference data** per Java class ("dump module")
- Reference data is emitted as **CSV**
- Pytest runs *TestDump* **once per session** using batch execution
- Results are cached and reused across tests

### Test Execution Flow

```
pytest
  └── collects tests with @pytest.mark.epq_ref
      └── builds batch of dump requests
          └── invokes CLI program once
              └── TestDump dispatches DumpModules
                  └── CSV emitted
          └── Python parses CSV and caches results
          └── individual tests run and verify results
```

## Directory Layout

```
project-root/
├── .epq-reference/
│   └── src/...                 # Java reference library (git submodule)
├── test/
│   ├── java/
│   │   ├── src/main/java/
│   │   │   └── epq/reference/
│   │   │       ├── TestDump.java
│   │   │       ├── DumpElement.java
│   │   │       ├── DumpXRayTransition.java
│   │   │       └── ... (other dump modules / helper classes)
│   │   ├── pom.xml
│   │   └── target/             # build artefacts
│   └── epq_dump/
│       ├── conftest.py         # pytest-Java bridge
│       ├── core_models.py      # Type definitions
│       ├── csv_parser.py       # Parser for CSV from TestDump
│       ├── test_*.py           # actual test files
│       └── validators.py       # Pydantic models to type check CSV
└── ...                         # other project files
```


## Test Filtering

The infrastructure respects Pytest's standard filtering:

```bash
# Run all tests except JVM-dependent tests
pytest -m "not epq_ref"

# Run only JVM-dependent tests
pytest -m "epq_ref"

# JVM will only start if tests marked @pytest.mark.epq_ref are selected
```

---

## Next Steps

- **Setting up**: See [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) for principles and design
- **Java API Reference**: See [JAVA_ORACLE_GUIDE.md](JAVA_ORACLE_GUIDE.md) for `TestDump`, `DumpModule`, `CsvWriter`
- **Pytest Integration**: See [PYTEST_BRIDGE_GUIDE.md](PYTEST_BRIDGE_GUIDE.md) for how fixtures and hooks work
- **How-To Guides**: See [TESTING_RECIPES.md](TESTING_RECIPES.md) to add new dump modules and write tests
