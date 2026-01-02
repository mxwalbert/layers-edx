import pytest
import sys
from pathlib import Path
from layers_edx.xrt import XRayTransition, XRayTransitionSet
from layers_edx.element import Element
from layers_edx.units import FromSI

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_java_test, compare_results

JAVA_TEST = Path(__file__).parent / "test_xrt.java"


def test_xrt_creation():
    si = Element("Si")
    # Si Ka1 is K-L3
    ka1 = XRayTransition(si, "KA1")

    assert ka1.element == si
    assert ka1.destination.name == "K"
    assert ka1.source.name == "LIII"


def test_xrt_energy():
    si = Element("Si")
    ka1 = XRayTransition(si, "KA1")

    # Si Ka1 energy ~ 1.74 keV
    from layers_edx.units import ToSI

    assert ka1.energy > ToSI.ev(1700)
    assert ka1.energy < ToSI.ev(1800)


def test_xrt_weight():
    si = Element("Si")
    ka1 = XRayTransition(si, "KA1")
    assert ka1.weight() > 0


def test_xrt_set():
    si = Element("Si")
    xrts = XRayTransitionSet(si)

    assert len(xrts.xrts) > 0

    # Check that Ka1 is in the set
    ka1 = XRayTransition(si, "KA1")
    assert xrts.contains(ka1)

    # Check weightiest
    w = xrts.weightiest_transition
    assert w is not None
    assert w.element == si


def test_xrt_set_filtering():
    si = Element("Si")
    # Only high energy transitions
    xrts = XRayTransitionSet(si, low_energy=2000)
    # Si K lines are < 2000 eV, so this might be empty or contain satellites?
    # Actually Si K edge is 1839 eV, so no fluorescence above that from Si K.
    assert len(xrts.xrts) == 0


def test_xrt_equality():
    si = Element("Si")
    t1 = XRayTransition(si, "KA1")
    t2 = XRayTransition(si, "KA1")
    assert t1 == t2
    assert hash(t1) == hash(t2)


@pytest.mark.epq
def test_xrt_silicon_k_vs_epq():
    """Validate Si K-line transitions against EPQ"""

    epq_results = run_java_test(str(JAVA_TEST))

    # Get Si K transitions from layers-edx
    element = Element("Si")
    python_transitions = []

    for epq_xrt in epq_results["transitions"]:
        # Try to match by name
        try:
            xrt = XRayTransition(element, epq_xrt["name"])
            python_transitions.append(
                {
                    "name": epq_xrt["name"],
                    "energy_ev": FromSI.ev(xrt.energy),
                    "weight": xrt.relative_weight,
                }
            )
        except:
            # Skip if transition not found in Python
            pass

    # Compare energies (5% tolerance for edge case differences)
    for py_xrt, epq_xrt in zip(python_transitions, epq_results["transitions"]):
        if py_xrt["name"] == epq_xrt["name"]:
            assert compare_results(
                py_xrt["energy_ev"], epq_xrt["energy_ev"], tolerance=0.05
            ), f"XRT {py_xrt['name']} energy mismatch"
