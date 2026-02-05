# Pytest-Java Bridge Guide

This document covers how pytest integrates with the Java reference oracle: the hook system, fixtures, and the internal data structures that make it all work.

## Architecture

The pytest-Java bridge operates in two main parts:

1. **Pytest Collection Hook** (`pytest_collection_modifyitems`): Collects all test markers, launches Java, parses results into a global cache
2. **Java Dump Fixture** (`java_dump`): Retrieves cached results for individual tests as lists of Pydantic model instances

Located in `test/epq_dump/conftest.py`.


## Core Components

### core_models.py

Defines the communication contract between pytest and Java.

#### DumpArgs

Type alias for dump arguments

```python
DumpArgs = Tuple[Tuple[str, str], ...] # e.g., (("Z", "26"), ("trans", "1"))
```

#### DumpRequest

A frozen dataclass that represents a request to Java

```python
@dataclass(frozen=True)
class DumpRequest:
    module: str            # e.g., "XRayTransition"
    args: DumpArgs

    def __post_init__(self):
        """Sort arguments by key name so ('Z','26') vs ('trans','1')
        always results in the same hash regardless of order in parametrize."""

    def to_batch_line(self) -> str:
        """Convert to batch mode format (sent to Java stdin)."""
```

Arguments are automatically sorted by key name:

```python
# Both produce identical hashes and batch lines
req1 = DumpRequest("XRayTransition", args=(("Z", "26"), ("trans", "1")))
req2 = DumpRequest("XRayTransition", args=(("trans", "1"), ("Z", "26")))

assert hash(req1) == hash(req2)
assert req1.to_batch_line() == req2.to_batch_line()
# Output: "XRayTransition Z=26 trans=1"
```

**Benefit**: Tests with different argument orders hit the same cache entry.

#### CsvTable

Type alias for a csv table

```python
CsvTable = List[Dict[str, str]]
```

## conftest.py

The "engine room" of the bridge.

### Global State

```python
# Populated during pytest_collection_modifyitems
# Maps requests to lists of Pydantic model instances
JAVA_ORACLE_DATA: Dict[DumpRequest, list[BaseModel]] = {}
```

### pytest_collection_modifyitems Hook

```python
@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """
    Collect DumpRequests from all selected tests.
    Launch Java once if any tests are marked @pytest.mark.epq_ref.
    """
```

**Timing**: Runs after other test filters, so:
- `pytest -m "not epq_ref"` → No Java launch
- `pytest test_foo.py::test_one` → Only tests in that file are collected

**Steps**:
1. Iterate over selected test items
2. For each test with `@pytest.mark.epq_ref(module="...")`:
   - Extract the module name
   - Generate `DumpRequest` objects from parametrize decorators
   - Deduplicate and accumulate requests
3. If any requests were collected:
   - Launch Java with batch mode
   - Parse framed CSV output
   - Validate with Pydantic models
   - Populate `JAVA_ORACLE_DATA` cache

### Marker Extraction

The collection hook extracts `DumpRequest` objects from test markers inline (not as a separate function). For each test:

```python
# Example test:
@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize("Z, trans", [(26, "1"), (79, "10")])
def test_xray(Z: int, trans: int, java_dump):
    ...

# Generates these DumpRequests:
[
    DumpRequest("XRayTransition", args=(("Z", "26"), ("trans", "1"))),
    DumpRequest("XRayTransition", args=(("Z", "79"), ("trans", "10"))),
]
```

**Logic**:
1. Check if test has `epq_ref` marker
2. Extract `module` from marker
3. Get all parametrize values (cartesian product if multiple decorators)
4. Convert parameters to strings (matching Java `key=value` format)
5. Create a `DumpRequest` for each combination

### Java Invocation: run_java_oracle_batch

```python
def run_java_oracle_batch(
    requests: Iterable[DumpRequest],
) -> dict[DumpRequest, CsvTable]:
    """Feeds all requests into Java via stdin and parses the result."""
    batch_input = "\n".join(r.to_batch_line() for r in requests) + "\n"

    java_project_root = (Path(__file__).parent.parent / "java").resolve()

    result = subprocess.run(
        [
            "mvn",
            "-q",
            "exec:java",
            "-Dexec.mainClass=epq.reference.TestDump",
            "-Dexec.args=batch",
        ],
        cwd=java_project_root,
        input=batch_input,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Java Oracle Failed:\n{result.stderr}")

    return dict(parse_epq_batch_output(result.stdout))
```

**Responsibilities**:
- Format all `DumpRequest` objects as batch input (one per line)
- Locate the Java project root directory
- Invoke Maven with batch mode and capture output
- Parse framed CSV output into a dictionary of results
- Raise `RuntimeError` if the Java process fails

**Called from**: `pytest_collection_modifyitems` during test collection

### CSV Frame Parsing

```python
def parse_request_table(stdout: str) -> Iterator[tuple[DumpRequest, FramedCsvTable]]:
    """
    Parse Java's framed CSV output.

    Input format:
        #BEGIN dump=XRayTransition Z=26 trans=1
        Energy,Intensity,Name
        6403.9,1.0,1
        #END

        #BEGIN dump=Element Z=79
        Energy
        91600.5
        #END

    Yields:
        (DumpRequest("XRayTransition", args=(("Z", "26"), ("trans", "1"))), [
            {"Energy": "6403.9", "Intensity": "1.0", "Name": "KA1"},
        ])
        (DumpRequest("Element", args=(("Z", "79"),)), [
            {"Energy": "91600.5"},
        ])
    """
```

**Logic**:
1. Split output on `#BEGIN` and `#END` markers
2. Extract request line: `dump=XRayTransition Z=26 trans=1`
3. Parse CSV lines until next `#END`
4. Reconstruct `DumpRequest` from request line
5. Parse CSV into list of dictionaries (intermediate format)
6. Cache under `DumpRequest` key (validation happens later in the fixture)


## java_dump Fixture

Retrieve the cached CSV result for the current test as a list of validated Pydantic model instances.

Uses pytest's StashKey to retrieve the DumpRequest stored during collection phase.


## Pydantic Schema Validation

The `java_dump` fixture automatically validates CSV data using Pydantic models. Each dump module has a corresponding Pydantic model that defines the expected schema.

The project includes validators in `test/epq_dump/validators.py`. For example, the `XRayTransition` dump uses the `XRayTransitionRow` model:

```python
from pydantic import BaseModel

class XRayTransitionRow(BaseModel):
    source_shell: str
    destination_shell: str
    family: str
    is_well_known: bool
    exists: bool
    # ... other fields
```

The validation happens automatically in the fixture—you receive already-validated model instances:

```python
import pytest
from test.epq_dump.validators import XRayTransitionRow

@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize("Z, trans", [(26, "1"), (79, "10")])
def test_xray_transition_schema(Z: int, trans: int, java_dump: list[XRayTransitionRow]):
    assert len(java_dump) > 0

    # Access validated model attributes directly
    assert java_dump[0].source_shell
    assert java_dump[0].family in ["K", "L", "M"]
```


**Scope**: `function` — runs once per test

**Error handling**:
- If test lacks `@pytest.mark.epq_ref`, raises `ValueError`
- If request not in cache, raises `KeyError` (indicates collector bug)


## Usage Examples

### Basic Golden Test

```python
import pytest
from test.epq_dump.validators import XRayTransitionRow

@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize("Z, trans", [
    (26, "KA1"),
    (79, "LA1"),
])
def test_xray_energies(Z: int, trans: str, java_dump: list[XRayTransitionRow]):
    """Verify xray energies against Java reference."""
    assert len(java_dump) > 0
    reference_energy = java_dump[0].energy_eV  # Direct attribute access

    result = my_model.calculate_energy(Z, trans)
    assert result == pytest.approx(reference_energy)
```

**Test run behavior**:
1. Pytest collects tests → `DumpRequest("XRayTransition", args=(("Z", "26"), ("trans", "KA1")))` and similar for other combinations
2. Before tests run → Java invoked with batch input
3. Java processes both requests, returns framed CSV
4. Results validated via Pydantic and cached in `JAVA_ORACLE_DATA`
5. First test runs → `java_dump` fixture returns validated Pydantic models for Z=26, trans=KA1
6. Second test runs → `java_dump` fixture returns validated Pydantic models for Z=79, trans=LA1

### Filtering Tests

```bash
# Run all tests, skip JVM-dependent ones
pytest -m "not epq_ref"

# Run only JVM-dependent tests
pytest -m "epq_ref"

# Run specific test file (may include JVM tests)
pytest test/python/test_xray.py

# Run specific test function
pytest test/python/test_xray.py::test_xray_energies
```

**Behavior**:
- If no `@pytest.mark.epq_ref` tests are selected → `pytest_collection_modifyitems` doesn't launch Java
- If at least one is selected → Java is launched once and results are cached for all

### Multiple Parametrize Dimensions

```python
@pytest.mark.epq_ref(module="XRayTransition")
@pytest.mark.parametrize("Z", [26, 79])
@pytest.mark.parametrize("trans", ["10", "11"])
@pytest.mark.parametrize("shell", ["K", "L"])
def test_combinations(Z: int, trans: int, shell: str, java_dump: list[XRayTransitionRow]):
    """
    Generates 2 * 2 * 2 = 8 test cases.
    Java is invoked once with 8 DumpRequests.
    """
    assert len(java_dump) > 0
```

Each combination generates a unique `DumpRequest`, but Java processes all at once.

---

## Troubleshooting

### Java process failed

**Symptom**: Test collection fails with `Java process failed`

**Debug steps**:
1. Run Java directly:
   ```bash
   cd test/java
   echo "XRayTransition Z=26 trans=KA1" | mvn exec:java -Dexec.mainClass=epq.reference.TestDump -Dexec.args="batch"
   ```
2. Check stderr for error message (e.g., "Unknown module: XRayTransition")
3. Verify `pom.xml` dependencies are installed

### Cache miss (KeyError)

**Symptom**: Test fails with `KeyError: No cached result for DumpRequest(...)`

**Causes**:
- Marker name or module name is incorrect
- Test parametrize values don't match what's expected
- DumpRequest was never extracted during collection

**Debug steps**:
1. Add print statement to fixture:
   ```python
   print(f"Looking for: {dump_request}")
   print(f"Cache keys: {JAVA_ORACLE_DATA.keys()}")
   ```
2. Verify marker syntax: `@pytest.mark.epq_ref(module="...")`
3. Ensure parametrize values are serializable to strings

### Test filter not working

**Symptom**: `pytest -m "not epq_ref"` still launches Java

**Cause**: Other plugins might add markers that trigger collection

**Fix**: Use `pytest -v` to see what tests are being collected, then investigate

---

## Architecture Diagram

```
pytest collection phase
    ↓
pytest_collection_modifyitems hook runs (trylast=True)
    ↓
extract @pytest.mark.epq_ref from selected tests
    ↓
build DumpRequest objects from parametrize values
    ↓
launch Java once with batch input
    ↓
parse framed CSV output
    ↓
populate JAVA_ORACLE_DATA cache
    ↓
pytest test phase
    ↓
for each test:
    java_dump fixture looks up DumpRequest in cache
    ↓
    test assertion runs
```
