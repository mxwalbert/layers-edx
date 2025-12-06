"""
Tests to verify EPQ environment setup for cross-validation testing.

This module tests that the EPQ Java library is properly installed and configured
according to the setup defined in conftest.py.
"""

import pytest
import subprocess
from pathlib import Path
import os


@pytest.mark.epq_env
def test_epq_classes_directory_exists():
    """Verify that EPQ compiled classes directory exists"""
    from test.conftest import epq_classes
    
    # This will either return the path or skip the test
    epq_path = epq_classes()
    assert epq_path is not None
    assert Path(epq_path).exists()
    assert Path(epq_path).is_dir()


@pytest.mark.epq_env
def test_epq_core_classes_compiled():
    """Verify that core EPQ library classes are compiled"""
    from test.conftest import epq_classes
    
    epq_path = Path(epq_classes())
    
    # Check for essential EPQ classes
    essential_classes = [
        "gov/nist/microanalysis/EPQLibrary/Element.class",
        "gov/nist/microanalysis/EPQLibrary/Composition.class",
        "gov/nist/microanalysis/EPQLibrary/ToSI.class",
        "gov/nist/microanalysis/EPQLibrary/AtomicShell.class",
    ]
    
    for class_file in essential_classes:
        full_path = epq_path / class_file
        assert full_path.exists(), f"Missing required EPQ class: {class_file}"


@pytest.mark.epq_env
def test_epq_dependencies_present():
    """Verify that EPQ Maven dependencies are present"""
    from test.conftest import epq_classes
    
    epq_path = Path(epq_classes())
    dependency_dir = epq_path.parent / "dependency"
    
    assert dependency_dir.exists(), "Dependency directory not found"
    
    # Check for critical dependencies
    jar_files = list(dependency_dir.glob("*.jar"))
    assert len(jar_files) > 0, "No dependency JARs found"
    
    # Check for specific required dependency (Jama)
    jama_jars = list(dependency_dir.glob("jama-*.jar"))
    assert len(jama_jars) > 0, "Jama dependency not found"


@pytest.mark.epq_env
def test_java_available():
    """Verify that Java is available in the environment"""
    result = subprocess.run(
        ['java', '-version'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Java not found in PATH"
    
    # Check Java version output (appears in stderr)
    version_output = result.stderr
    assert 'version' in version_output.lower(), "Invalid Java version output"


@pytest.mark.epq_env
def test_javac_available():
    """Verify that Java compiler is available in the environment"""
    result = subprocess.run(
        ['javac', '-version'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Java compiler (javac) not found in PATH"


@pytest.mark.epq_env
def test_java_compilation_with_epq():
    """Test that we can compile a simple Java program using EPQ classes"""
    from test.conftest import epq_classes
    import tempfile
    
    epq_path = Path(epq_classes())
    
    # Build classpath
    classpath_parts = [str(epq_path)]
    dependency_dir = epq_path.parent / "dependency"
    if dependency_dir.exists():
        for jar_file in dependency_dir.glob("*.jar"):
            classpath_parts.append(str(jar_file))
    
    classpath = os.pathsep.join(classpath_parts)
    
    # Create a simple test Java file
    test_code = """
import gov.nist.microanalysis.EPQLibrary.Element;

public class EPQTest {
    public static void main(String[] args) {
        Element si = Element.Si;
        System.out.println(si.toAbbrev());
    }
}
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "EPQTest.java"
        test_file.write_text(test_code)
        
        # Compile
        compile_result = subprocess.run(
            ['javac', '-cp', classpath, str(test_file), '-d', tmpdir],
            capture_output=True,
            text=True
        )
        
        assert compile_result.returncode == 0, \
            f"Failed to compile test Java file:\n{compile_result.stderr}"
        
        # Verify .class file was created
        class_file = Path(tmpdir) / "EPQTest.class"
        assert class_file.exists(), "Compiled .class file not found"


@pytest.mark.epq_env
def test_run_java_test_helper():
    """Test the run_java_test helper function from conftest.py"""
    from test.conftest import run_java_test
    import tempfile
    
    # Create a simple Java test that outputs JSON
    test_code = """
public class JSONTest {
    public static void main(String[] args) {
        System.out.println("{\\\"result\\\": \\\"success\\\", \\\"value\\\": 42}");
    }
}
"""
    
    # Create temporary directory and properly named file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "JSONTest.java"
        test_file.write_text(test_code)
        
        result = run_java_test(str(test_file))
        
        assert isinstance(result, dict), "run_java_test should return a dict"
        assert result["result"] == "success"
        assert result["value"] == 42


@pytest.mark.epq_env
def test_compare_results_helper():
    """Test the compare_results helper function from conftest.py"""
    from test.conftest import compare_results
    import numpy as np
    
    # Test scalar comparison
    assert compare_results(1.0, 1.0)
    assert compare_results(1.0, 1.005, tolerance=0.01)
    assert not compare_results(1.0, 1.05, tolerance=0.01)
    
    # Test array comparison
    py_arr = np.array([1.0, 2.0, 3.0])
    java_arr = np.array([1.005, 2.005, 3.005])
    assert compare_results(py_arr, java_arr, tolerance=0.01)
    
    # Test list comparison
    py_list = [1.0, 2.0, 3.0]
    java_list = [1.005, 2.005, 3.005]
    assert compare_results(py_list, java_list, tolerance=0.01)
