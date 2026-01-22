import csv
import io
from typing import Iterable, List, Tuple
from test.epq_dump.core_models import CsvTable, DumpRequest



def parse_epq_batch_output(
    output: str,
) -> Iterable[tuple[DumpRequest, CsvTable]]:
    """
    Yields (DumpRequest, list of dictionaries) pairs from framed CSV output.
    """
    current_header = None
    current_csv = []

    for line in output.splitlines():
        line = line.rstrip()

        if line.startswith("#BEGIN"):
            if current_header is not None:
                raise RuntimeError("Nested #BEGIN detected")

            current_header = line
            current_csv: List[str] = []
            continue

        if line == "#END":
            if current_header is None:
                raise RuntimeError("#END without #BEGIN")

            req = parse_begin_header(current_header)
            table = parse_csv_block(current_csv)
            yield req, table

            current_header = None
            current_csv = []
            continue

        if current_header is not None:
            current_csv.append(line)

    if current_header is not None:
        raise RuntimeError("Unterminated #BEGIN block")


def parse_begin_header(line: str) -> DumpRequest:
    """
    Parse:
      #BEGIN dump=XRayTransition Z=26 trans=KA1
    """
    tokens = line.split()
    if tokens[0] != "#BEGIN":
        raise ValueError(f"Invalid BEGIN line: {line}")

    module = None
    args: List[Tuple[str, str]] = []

    for tok in tokens[1:]:
        if tok.startswith("dump="):
            module = tok[len("dump=") :]
        else:
            if "=" not in tok:
                raise ValueError(f"Invalid BEGIN token: {tok}")
            k, v = tok.split("=", 1)
            args.append((k, v))

    if module is None:
        raise ValueError(f"Missing dump name in BEGIN line: {line}")

    return DumpRequest(module=module, args=tuple(args))


def parse_csv_block(lines: List[str]) -> CsvTable:
    """Parse CSV lines into a list of dictionaries."""
    if not lines:
        return []

    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    return list(reader)
