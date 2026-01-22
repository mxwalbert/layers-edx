# Testing Architecture

This document covers the design principles, three-phase execution model, and the CSV contract that bridges Java and Python.

## Design Principles

### Why Golden Testing?

The approach treats Java as the authoritative reference. Python tests verify that the port produces identical results for the same inputs. This provides:

- **Correctness by construction**: Any discrepancy is caught immediately
- **Confidence during refactoring**: Behavioral changes are visible
- **Language-agnostic validation**: Porting errors are detected, not implementation bugs
- **Single JVM invocation**: Batch execution minimizes startup cost

### Determinism and Reproducibility

All components enforce deterministic behavior:

- Argument order is preserved (not sorted)
- CSV output uses fixed column order
- Floating-point formatting is locale-independent (`Locale.ROOT`)
- Scientific notation: `"%.12e"` for all floats
- Duplicate arguments are rejected

This ensures that the same test produces identical results across runs, making diffs meaningful and results cacheable.

## Three-Phase Execution Model

### Phase 1: Collection (Python)

**When**: During pytest collection (before any tests run)

**What happens**:
1. Pytest discovers all test functions marked with `@pytest.mark.epq_ref`
2. The `pytest_collection_modifyitems` hook (in `conftest.py`) extracts `DumpRequest` objects from each test's marker and arguments from parametrize decorators
3. All unique requests are deduplicated and accumulated

**Why**: By collecting all requests upfront, we can batch them and minimize JVM startup cost.

### Phase 2: Execution (Java)

**When**: Before any tests execute

**What happens**:
1. Pytest launches ClI program *Testdump*
2. All collected `DumpRequest` objects are converted to **batch mode** format (one request per line)
3. Requests are written to `stdin` of the Java process
4. The Java process parses each request, dispatches to the appropriate `DumpModule`, and emits *framed* CSV output
5. All output is captured and parsed into a global cache (`JAVA_ORACLE_DATA`)


### Phase 3: Verification (Python)

**When**: As tests execute

**What happens**:
1. Each test function receives the `java_dump` fixture
2. The fixture retrieves the pre-computed CSV results from the global cache
3. The test verifies its specific assertions against the reference data

**Why**: Tests run fast because all JVM interactions are batched and cached.

## Canonicalization and Deduplication

`DumpRequest` automatically sorts arguments by key name. This ensures:
- `(Z=26, trans=1)` and `(trans=1, Z=26)` map to the same request
- Only one Java call is made for both cases
- Requests are deterministic and cacheable


## CSV as the Wire Format

### Why CSV?

CSV is the contract between Java and Python. It was chosen because:

- **Stable**: Schema is explicit
- **Diff-friendly**: Human-readable, easy to review changes
- **Human-readable**: Can be inspected manually for debugging
- **Easy to parse**: Python has robust CSVReader()

### CSV Guarantees

1. **Fixed column order**: Determined by the `DumpModule` at emission time
2. **Locale independence**: Uses `Locale.ROOT` for formatting
3. **Scientific notation**: Floating-point numbers use `"%.12e"` format
4. **Header row**: First row names all columns
5. **No embedded quotes**: Values are never quoted (simplifies parsing)

### Example

```csv
Z,Energy,TransitionName
26,6403.9,KA1
26,5889.8,KA2
79,91600.5,LA1
```

## Error Handling and Propagation

### Error Flow

```
DumpModule.run(ctx)
    ↓
    ├─ Syntax Error (argument parsing)
    │   → DumpContext throws IllegalArgumentException
    │   → TestDump catches, prints error message and usage
    │   → Exit code 1
    │
    └─ Semantic Error (validation failure)
        → DumpModule throws IllegalArgumentException
        → TestDump catches, prints error message and module usage
        → Exit code 1
```

### User-Facing Errors

All user errors are handled centrally by `TestDump`:
- Unknown dump module name
- Missing required arguments
- Argument parsing errors (malformed key=value)
- Semantic validation failures (invalid enum value, out-of-range Z)

**Behavior**:
- Print error message (no stack trace)
- Print module usage
- Exit with code 1

### No Java Stack Traces

For user errors, no Java exception stack trace is emitted. The error message is human-readable and actionable.

For infrastructure errors (e.g., Maven not found, IO exceptions), stderr will contain the actual Java exception.

## Batch Mode Protocol

### Command

```bash
mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="batch"
```

### Input (stdin)

One request per line. Each request has the format:

```
<module-name> [key=value] [key=value] ...
```

Example:
```
XRayTransition Z=26 trans=1
XRayTransition Z=79 trans=2
Element Z=6
```

### Output (stdout)

Requests are framed with markers:

```
#BEGIN dump=<request-line>
<csv-header>
<csv-row-1>
<csv-row-2>
...
#END

#BEGIN dump=<next-request-line>
...
```

### Frame Parsing

Python parses frames by:
1. Reading lines until `#BEGIN dump=...` is found
2. Extracting the request (after `dump=`)
3. Collecting CSV lines until `#END` is found
4. Parsing CSV lines into a list of dictionaries
5. Caching the result keyed by `DumpRequest`

---

## Future Extensions

- **Configuration**: Per-module allowed-argument validation
- **Type safety**: Typed getters in `DumpContext` (`getInt()`, `getDouble()`)
- **Output formats**: JSON or metadata support
- **Performance**: Optional caching to disk between test runs
