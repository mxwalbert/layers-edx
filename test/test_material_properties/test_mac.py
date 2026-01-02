import pytest
import sys
from pathlib import Path
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI

# Add parent directory to path to import from conftest
sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_java_test, compare_results

# Path to corresponding Java test
JAVA_TEST = Path(__file__).parent / "test_mac.java"


def test_mac_element():
    si = Element("Si")
    energy = ToSI.kev(1.74)  # Si Ka energy

    # MAC of Si for Si Ka should be significant
    mac = MassAbsorptionCoefficient.compute(si, energy)
    assert mac > 0

    # MAC decreases with energy (away from edges)
    mac_high = MassAbsorptionCoefficient.compute(si, ToSI.kev(10.0))
    assert mac > mac_high


def test_mac_composition():
    si = Element("Si")
    o = Element("O")
    sio2 = Composition([si, o], [1.0, 2.0], weight=False)
    energy = ToSI.kev(1.74)

    mac_sio2 = MassAbsorptionCoefficient.compute_composition(sio2, energy)
    mac_si = MassAbsorptionCoefficient.compute(si, energy)
    mac_o = MassAbsorptionCoefficient.compute(o, energy)

    # MAC of composition is weighted average
    w_si = sio2.weight_fractions[si]
    w_o = sio2.weight_fractions[o]
    expected = w_si * mac_si + w_o * mac_o

    assert mac_sio2 == pytest.approx(expected)


@pytest.mark.epq
def test_mac_silicon_energies_vs_epq():
    """Validate Python MAC against EPQ for Silicon at various energies"""

    # Run Java EPQ test
    epq_results = run_java_test(str(JAVA_TEST))

    # Run Python implementation
    element = Element("Si")
    energies_kev = [1.0, 1.74, 5.0, 10.0, 20.0]

    python_results = []
    for energy_kev in energies_kev:
        mac = MassAbsorptionCoefficient.compute(element, ToSI.kev(energy_kev))
        python_results.append(mac)

    # Compare with 1% tolerance
    assert compare_results(
        python_results, epq_results["silicon_energies"], tolerance=0.01
    ), f"MAC mismatch: Python={python_results}, EPQ={epq_results['silicon_energies']}"


@pytest.mark.epq
def test_mac_sio2_vs_epq():
    """Validate Python MAC for SiO2 composition against EPQ"""

    # Run Java EPQ test
    epq_results = run_java_test(str(JAVA_TEST))

    # Run Python implementation
    elements = [Element("Si"), Element("O")]
    fractions = [0.467, 0.533]  # weight fractions
    comp = Composition(elements, fractions, weight=True)

    python_mac = MassAbsorptionCoefficient.compute_composition(comp, ToSI.kev(1.74))

    # Compare with 2% tolerance (compositions may have more variance)
    assert compare_results(python_mac, epq_results["sio2_at_si_ka"], tolerance=0.02), (
        f"SiO2 MAC mismatch: Python={python_mac}, EPQ={epq_results['sio2_at_si_ka']}"
    )
