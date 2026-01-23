# Cross-Language Testing Strategy (Java → Python Port)

This project is a **full Python port** of the Java library [Electron Probe Quantification (EPQ)](https://github.com/usnistgov/EPQ) by NIST.

To ensure correctness, the Python implementation is continuously tested against the original Java behavior using a **reference dump strategy** (Golden Testing). The Java code is treated as an **oracle**, and Python tests verify that the ported implementation produces equivalent observable results.

## Overview

### How it works

- The original Java code is **not modified** only compiled
- A small **CLI program** called *TestDump* provides an interface to instantiate Java classes
- *TestDump* emits **deterministic reference data** per Java class ("dump module")
- Reference data is emitted as **CSV**, where each data set is framed for easier parsing
- *TestDump* is run **once per session** using batch execution 
- Results are cached and reused across tests

### Test Execution Flow

Tests are collected and run with `Pytest`. Tests which need reference data are marked

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

The reference library is added as git submodule at .epq-reference/\
Testfiles for Python and Java CLI Source files are in test/


```
project-root/
├── .epq-reference/             # Java reference library (git submodule)
│   └── ...
├── test/
│   ├── java/                   # Java side of testing (CLI program)
│   │   ├── src/main/java/      # Directory structure as expected by Maven
│   │   │   └── epq/reference/  # Java source files
│   │   │       └── ...
│   │   ├── pom.xml             # Project file for Maven
│   │   └── target/             # build artefacts
│   │       └── ...
│   └── epq_dump/               # Pytest side of testing (Parse CSV output, run tests)
│       └── ...
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
