#!/usr/bin/env python3
"""
Setup script for EPQ Java library.

This script:
1. Reads the EPQ version from a centralized config
2. Generates pom.xml from pom.template with the correct version
3. Compiles the EPQ library
4. Installs it locally to the Maven repository
5. Updates the test/java/pom.xml with the same version
"""

import subprocess
import sys
from pathlib import Path

# Import EPQ version from config file (single source of truth)
from epq_config import EPQ_VERSION


def run_command(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"


def create_pom_from_template(epq_dir: Path, version: str) -> bool:
    """Create pom.xml from pom.template with the specified version."""
    template_file = epq_dir / "pom.template"
    pom_file = epq_dir / "pom.xml"

    if not template_file.exists():
        print(f"❌ Template file not found: {template_file}")
        return False

    print("📝 Creating pom.xml from template...")
    try:
        template_content = template_file.read_text()
        pom_content = template_content.replace("NUMBER_VERSION", version)
        pom_file.write_text(pom_content)
        print(f"✅ Created {pom_file} with version {version}")
        return True
    except Exception as e:
        print(f"❌ Failed to create pom.xml: {e}")
        return False


def update_test_pom(test_pom_path: Path, version: str) -> bool:
    """Update the test/java/pom.xml with the correct EPQ version."""
    if not test_pom_path.exists():
        print(f"⚠️  Test pom.xml not found at {test_pom_path}")
        return False

    print("📝 Updating test pom.xml...")
    try:
        content = test_pom_path.read_text()
        updated_content = content.replace("NUMBER_VERSION", version)
        test_pom_path.write_text(updated_content)
        print(f"✅ Updated {test_pom_path} with version {version}")
        return True
    except Exception as e:
        print(f"❌ Failed to update test pom.xml: {e}")
        return False


def compile_epq(epq_dir: Path) -> bool:
    """Compile the EPQ library using Maven."""
    print("\n🔨 Compiling EPQ library...")
    success, output = run_command(["mvn", "compile"], epq_dir)

    if success:
        print("✅ EPQ compiled successfully!")
        return True
    else:
        print(f"❌ Compilation failed:\n{output}")
        return False


def install_epq_locally(epq_dir: Path) -> bool:
    """Install the EPQ library to the local Maven repository."""
    print("\n📦 Installing EPQ library to local Maven repository...")
    success, output = run_command(["mvn", "install"], epq_dir)

    if success:
        print("✅ EPQ installed successfully to local Maven repository!")
        return True
    else:
        print(f"❌ Installation failed:\n{output}")
        return False


def main():
    """Main setup function."""
    print("=" * 70)
    print("EPQ Library Setup Script")
    print(f"Version: {EPQ_VERSION}")
    print("=" * 70)

    # Determine paths
    script_dir = Path(__file__).parent
    workspace_dir = script_dir.parent
    epq_dir = workspace_dir / ".epq-reference"
    test_pom = workspace_dir / "test" / "java" / "pom.xml"

    # Check if EPQ submodule directory exists
    if not epq_dir.exists():
        print(f"❌ EPQ directory not found: {epq_dir}")
        print("This should not happen - the submodule path should exist.")
        return 1

    # Check if EPQ submodule is empty (not initialized)
    if not any(epq_dir.iterdir()):
        print("EPQ submodule directory is empty. Initializing submodule...")
        success, output = run_command(
            ["git", "submodule", "update", "--init", ".epq-reference"],
            workspace_dir
        )
        if not success:
            print(f"❌ Failed to initialize submodule:\n{output}")
            return 1
        print("EPQ submodule initialized successfully!")
    else:
        print(f"EPQ submodule found at {epq_dir}")

    # Check for Maven
    try:
        subprocess.run(["mvn", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Maven not found. Please install Maven first.")
        return 1

    print(f"\n📂 EPQ directory: {epq_dir}")
    print(f"📂 Test pom.xml: {test_pom}")

    # Step 1: Create pom.xml from template
    if not create_pom_from_template(epq_dir, EPQ_VERSION):
        return 1

    # Step 2: Update test pom.xml
    if not update_test_pom(test_pom, EPQ_VERSION):
        print("⚠️  Warning: Could not update test pom.xml")
        # Don't fail - continue with EPQ setup

    # Step 3: Compile EPQ
    if not compile_epq(epq_dir):
        return 1

    # Step 4: Install EPQ locally
    if not install_epq_locally(epq_dir):
        return 1

    print("\n" + "=" * 70)
    print("✅ EPQ setup complete!")
    print("=" * 70)
    print(f"EPQ version {EPQ_VERSION} is now installed in your local Maven repository.")
    print("You can now build and run tests in test/java/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
