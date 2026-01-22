#!/usr/bin/env python
"""
Script to run the EPQ TestDump utility via Maven.

Usage:
    python run_testdump.py module arg1=value1 arg2=value2
    python run_testdump.py batch < input.txt
"""

import subprocess
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run EPQ TestDump utility via Maven",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_testdump.py module arg1=value1 arg2=value2
  python run_testdump.py batch < input.txt
  echo "module arg1=value1 arg2=value2" | python run_testdump.py batch
        """,
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments to pass to TestDump (e.g., 'batch', 'dump', or custom args)",
    )

    args = parser.parse_args()

    # Build the exec args for Maven
    exec_args = " ".join(args.args) if args.args else ""

    # Get the java project root (scripts/../test/java)
    scripts_dir = Path(__file__).resolve().parent
    java_project_root = (scripts_dir.parent / "test" / "java").resolve()

    if not java_project_root.exists():
        print(
            f"Error: Java project root not found at {java_project_root}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build and run the Maven command
    cmd = [
        "mvn",
        "-q",
        "exec:java",
        "-Dexec.mainClass=epq.reference.TestDump",
    ]

    if exec_args:
        cmd.append(f"-Dexec.args={exec_args}")

    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    print(f"Working directory: {java_project_root}", file=sys.stderr)

    result = subprocess.run(
        cmd,
        cwd=java_project_root,
        text=True,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
