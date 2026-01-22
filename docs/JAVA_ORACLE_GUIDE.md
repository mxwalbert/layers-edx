# Java Oracle Guide

This document is a complete reference for the Java components that implement the CLI program wich acts as reference oracle: `TestDump`, `DumpContext`, `CsvWriter`, and `DumpModule`.

## Environment Setup

Before using the Java oracle, you must set up the EPQ Java library. This section covers configuration and installation using the scripts provided in the `scripts/` directory.

### Quick Start

Use the Python setup script (recommended):

```bash
python scripts/setup_epq.py
```

This script will:
1. Read the EPQ version from `epq_config.py`
2. Generate `pom.xml` from `pom.template` with the correct version for EPQ
3. Update `test/java/pom.xml` with the same version
4. Compile the EPQ library
5. Install it to your local Maven repository (~/.m2/repository)

**Note:** The `test/java/pom.xml` file is tracked in git with a `NUMBER_VERSION` placeholder. Local changes can be ignored using `git update-index --skip-worktree`. This allows the setup script to update it with the actual version without affecting git status.

### Prerequisites

- **Java 21 or higher**
- **Maven 3.6 or higher**
- **EPQ repository** cloned to `.epq-reference/` directory

If you haven't cloned the EPQ repository yet, run:

```bash
git clone https://github.com/usnistgov/EPQ.git .epq-reference
```

Or use the bash script to do everything including cloning:

```bash
bash scripts/setup_epq.sh
```

### Configuration

EPQ version management is centralized in `scripts/epq_config.py`. This file stores the EPQ version number as a single source of truth.

To update the EPQ version used throughout the project:

1. Edit `scripts/epq_config.py` and change the `EPQ_VERSION` value
2. Run `python3 scripts/setup_epq.py` to regenerate pom.xml files and reinstall

This ensures the version is consistent across:
- `.epq-reference/pom.xml` (EPQ library itself)
- `test/java/pom.xml` (test code that depends on EPQ)

### Manual Setup Steps

If you need to perform individual steps manually:

**Generate pom.xml from template:**

```bash
cd .epq-reference
sed "s/NUMBER_VERSION/15.1.43/g" pom.template > pom.xml
```

**Compile EPQ:**

```bash
cd .epq-reference
mvn compile
```

**Install EPQ to local Maven repository:**

```bash
cd .epq-reference
mvn install
```

This installs the EPQ JAR to `~/.m2/repository/gov/nist/microanalysis/epq/` where it can be used as a dependency by other Maven projects.

### Troubleshooting

**Java version mismatch:**

EPQ requires Java 21 or higher. Check your Java version:

```bash
java -version
```

**Maven not found:**

Install Maven from https://maven.apache.org/download.cgi

**EPQ repository not found:**

Make sure the EPQ repository is cloned to `.epq-reference/`:

```bash
git clone https://github.com/usnistgov/EPQ.git .epq-reference
```

**Compilation errors:**

Make sure you're using Java 21 or higher and that the pom.xml has been generated.

**Git showing changes to test/java/pom.xml:**

If you need to re-enable git tracking of local changes:

```bash
git update-index --no-skip-worktree test/java/pom.xml
```

To ignore local changes again:

```bash
git update-index --skip-worktree test/java/pom.xml
```

---

## Using run_testdump.py

For convenience, the `scripts/run_testdump.py` helper script provides a simpler interface to invoke `TestDump` without needing to remember the full Maven command syntax.

### Usage

```bash
python scripts/run_testdump.py <module> [arg1=value1] [arg2=value2] ...
```

### Examples

**Single invocation:**

```bash
python scripts/run_testdump.py Element Z=1
python scripts/run_testdump.py XRayTransition Z=26 trans=1
```

**Batch mode (read from stdin):**

```bash
echo "Element Z=1" | python scripts/run_testdump.py batch
```

**Multiple batch requests:**

```bash
cat << EOF | python scripts/run_testdump.py batch
Element Z=1
Element Z=79
XRayTransition Z=26 trans=1
EOF
```

### How It Works

The script:
1. Takes all command-line arguments and joins them with spaces
2. Passes them to `TestDump` via Maven's `-Dexec.args` parameter
3. Automatically finds the Java project root directory
4. Runs Maven from the correct working directory
5. Logs the command and working directory to stderr for debugging
6. Exits with the same return code as Maven

---

## Overview

All Java reference dumps are accessed via a **single CLI entry point**:

```bash
mvn exec:java \
  -Dexec.mainClass=epq.reference.TestDump \
  -Dexec.args="<command> [args...]"
```

Each dump module interprets its own arguments, emits exactly one CSV table, and contains no shared domain logic.

---

## TestDump

`TestDump` is the **single Java entry point** for all golden-test dumps. Located at `test/java/src/main/java/epq/reference/TestDump.java`.

### Responsibilities

- Acts as a CLI dispatcher
- Routes requests to the appropriate `DumpModule`
- Handles single vs batch execution modes
- Owns all process-exit behavior
- Prints usage and error messages
- Emits framing markers in batch mode

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (invalid module name, missing arguments, validation failure) |
| 2 | Infrastructure error (IO exception, Maven not found) |

### Invocation Modes

#### Single Mode (Human-Facing)

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="XRayTransition Z=26 trans=KA1"
```

**Output**: Raw CSV only (no framing markers)

```csv
Energy,EdgeEnergy,OccupancyNumber
6403.9,123.4,2
```

**Use case**: Debugging, manual inspection, shell scripting

#### Batch Mode (Machine-Facing)

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="batch"
```

**Input**: `stdin`, one request per line

```
XRayTransition Z=26 trans=KA1
EdgeEnergy Z=79
```

**Output**: Framed CSV blocks (see [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) for format)

```
#BEGIN dump=XRayTransition Z=26 trans=KA1
Energy,EdgeEnergy,OccupancyNumber
6403.9,123.4,2
#END
#BEGIN dump=EdgeEnergy Z=79
Energy
91600.5
#END
```

**Use case**: Pytest integration, batch processing

---

## DumpContext

`DumpContext` represents the **execution context for a single dump invocation**. Located at `test/java/src/main/java/epq/reference/DumpContext.java`.

It is deliberately small and generic. Think of it as a "request container" with argument parsing and CSV output helpers.

### Responsibilities

- Parse `key=value` arguments from the command line
- Preserve deterministic argument order
- Provide argument accessors (required and optional)
- Own CSV output helpers
- Manage CSV flushing

### Argument Parsing

Arguments must be of the form `key=value`:

```
TestDump XRayTransition Z=26 trans=KA1
                         ^  ^  ^      ^
                         key = value (repeated)
```

**Validation**:
- Arguments must match pattern `key=value`
- Duplicate keys are rejected
- Syntax errors result in `IllegalArgumentException`

### Argument Access

```java
// Required argument - throws if not present
String z = ctx.get("Z");

// Optional argument with default
String trans = ctx.getOrDefault("trans", "KA1");

// Read-only view of all arguments
Map<String, String> args = ctx.args();
```

### CSV Output

`DumpContext` exposes an instance of `CsvWriter` via `csv()`:

```java
CsvWriter csv = ctx.csv();
csv.header("Z", "Energy", "TransitionName");
csv.row("26", "6403.9", "KA1");
csv.row("26", "5889.8", "KA2");
csv.flush();
```

**Output**:
```csv
Z,Energy,TransitionName
26,6403.9,KA1
26,5889.8,KA2
```

---

## CsvWriter

A simple CSV writer utility. Located at `test/java/src/main/java/epq/reference/CsvWriter.java`.

### Responsibilities

- Write deterministic CSV output
- Enforce fixed column order
- Apply locale-independent formatting

### Design

- **Fixed column order**: Set at `header()` time; all subsequent `row()` calls must match
- **Locale.ROOT**: All formatting uses `Locale.ROOT` (no local decimal separators)
- **Scientific notation**: Floating-point numbers use `"%.12e"` format
- **No quoting**: Values are never quoted (simplifies parsing)

### API

```java
CsvWriter csv = new CsvWriter(System.out);  // or any OutputStream

// Set column names
csv.header("Z", "Energy", "OccupancyNumber");

// Write rows
csv.row("26", "6403.9", "2");
csv.row("79", "91600.5", "10");

// Flush output
csv.flush();
```

### Scientific Notation Example

```java
csv.header("Element", "Value");
csv.row("Iron", String.format(Locale.ROOT, "%.12e", 1.23456789));
// Output: 1.234567890000e+00
```

---

## DumpModule

`DumpModule` represents **one dumpable unit of reference behavior**. Each module corresponds roughly to one EPQ concept (e.g., `XRayTransition`, `EdgeEnergy`).

Located at `test/java/src/main/java/epq/reference/DumpModule.java` (interface) and implementations like `test/java/src/main/java/epq/reference/XRayTransitionDump.java`.

### Interface

```java
public interface DumpModule {
    /// Module command name (e.g., "XRayTransition")
    String name();

    /// Human-readable usage string
    String usage();

    /// Execute the dump, parse arguments, emit CSV
    /// @throws IllegalArgumentException if arguments are invalid
    void run(DumpContext ctx) throws IllegalArgumentException;
}
```

### Responsibilities

A `DumpModule`:

- Defines its command name
- Declares its usage string (human-readable, shown on error)
- Parses and validates its own arguments
- Executes reference logic
- Emits CSV via `DumpContext.csv()`

### Example: Simple XRayTransitionDump

```java
public class XRayTransitionDump implements DumpModule {
    @Override
    public String name() {
        return "XRayTransition";
    }

    @Override
    public String usage() {
        return "XRayTransition Z=<element> trans=<transition>";
    }

    @Override
    public void run(DumpContext ctx) throws IllegalArgumentException {
        // Parse arguments
        int z = Integer.parseInt(ctx.get("Z"));
        String transition = ctx.get("trans");

        // Validate
        if (z < 1 || z > 118) {
            throw new IllegalArgumentException("Z must be 1-118");
        }

        // Fetch reference data
        XRaySet transitions = EPQ.getXRayTransitions(z);
        XRayTransition xrt = transitions.getTransition(transition);
        if (xrt == null) {
            throw new IllegalArgumentException("Unknown transition: " + transition);
        }

        // Emit CSV
        CsvWriter csv = ctx.csv();
        csv.header("Energy", "Intensity", "Name");
        csv.row(
            String.format(Locale.ROOT, "%.12e", xrt.getEnergy()),
            String.format(Locale.ROOT, "%.12e", xrt.getWeight()),
            xrt.toString()
        );
        csv.flush();
    }
}
```

### Argument Validation Model

Two-tier error handling:

1. **Syntax errors** (argument parsing):
   - Handled by `DumpContext` in constructor
   - Throws `IllegalArgumentException` if `key=value` format is malformed
   - Thrown immediately, before `DumpModule.run()` is called

2. **Semantic errors** (validation):
   - Handled by `DumpModule.run()`
   - Throws `IllegalArgumentException` if arguments are valid syntax but invalid values
   - Caught by `TestDump`, which decides how to surface the error

### Example Error Flow

```java
// Syntax error: caught before run()
ctx.get("Z");  // argument doesn't exist → IllegalArgumentException

// Semantic error: caught during run()
int z = Integer.parseInt(ctx.get("Z"));  // valid syntax
if (z < 1 || z > 118) {
    throw new IllegalArgumentException("Z out of range");
}
```

### Error Propagation

1. `DumpModule.run()` throws `IllegalArgumentException`
2. `TestDump` catches it
3. If in single mode, prints module usage and error message
4. If in batch mode, prints framing marker with error note
5. Exit code is always 1

---

## Registering a New DumpModule

To add a new dump module:

1. Create a class implementing `DumpModule` in `test/java/src/main/java/epq/reference/`
2. Implement `name()`, `usage()`, and `run()`
3. Register it in `TestDump.getDumpModules()`

Example:

```java
// In TestDump.java
private static Map<String, DumpModule> getDumpModules() {
    return Map.ofEntries(
        Map.entry("XRayTransition", new XRayTransitionDump()),
        Map.entry("EdgeEnergy", new EdgeEnergyDump()),
        Map.entry("Element", new ElementDump()),  // NEW
        // ...
    );
}
```

---

## Maven Layout

This project uses the standard Maven layout:

```
test/java/
├── src/main/java/
│   └── epq/reference/
│       ├── TestDump.java
│       ├── DumpContext.java
│       ├── CsvWriter.java
│       ├── DumpModule.java
│       └── (implementations)
├── pom.xml
└── build/classes/
```

**Benefits**:
- Zero custom build configuration
- Maximum IDE and tooling compatibility
- Fewer failure modes when invoking Maven from pytest or CI
- Standard Maven plugins work out of the box
