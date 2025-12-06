import pytest
import sys
from pathlib import Path
from layers_edx.material_properties.mip import MeanIonizationPotential
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI, FromSI

# Add parent directory to path to import from conftest
sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_java_test, compare_results

# Path to corresponding Java test
JAVA_TEST = Path(__file__).parent / "test_mip.java"


def test_mip_element():
    si = Element('Si')
    mip = MeanIonizationPotential.compute(si)
    assert mip > 0
    # MIP for Si (Z=14) is approx 173 eV
    assert mip == pytest.approx(ToSI.ev(173), rel=0.1)


def test_mip_composition():
    si = Element('Si')
    o = Element('O')
    sio2 = Composition([si, o], [1.0, 2.0], weight=False)
    
    mip = MeanIonizationPotential.compute_composition(sio2)
    assert mip > 0
    
    # Should be between MIP of Si and O
    mip_si = MeanIonizationPotential.compute(si)
    mip_o = MeanIonizationPotential.compute(o)
    
    assert min(mip_si, mip_o) < mip < max(mip_si, mip_o)


@pytest.mark.epq
def test_mip_elements_vs_epq():
    """Validate Python MIP against EPQ for various elements"""
    
    # Run Java EPQ test
    epq_results = run_java_test(str(JAVA_TEST))
    
    # Run Python implementation
    element_symbols = epq_results['elements']  # ['Si', 'O', 'Fe', 'Au']
    python_results = []
    
    for symbol in element_symbols:
        element = Element(symbol)
        mip_j = MeanIonizationPotential.compute(element)
        mip_ev = FromSI.ev(mip_j)
        python_results.append(mip_ev)
    
    # Compare with 2% tolerance (MIP calculations can vary slightly)
    assert compare_results(
        python_results,
        epq_results['element_mips'],
        tolerance=0.02
    ), f"MIP mismatch: Python={python_results}, EPQ={epq_results['element_mips']}"


@pytest.mark.epq
def test_mip_sio2_vs_epq():
    """Validate Python MIP for SiO2 composition against EPQ"""
    
    # Run Java EPQ test
    epq_results = run_java_test(str(JAVA_TEST))
    
    # Run Python implementation
    elements = [Element('Si'), Element('O')]
    fractions = [0.467, 0.533]  # weight fractions
    comp = Composition(elements, fractions, weight=True)
    
    python_mip_j = MeanIonizationPotential.compute_composition(comp)
    python_mip_ev = FromSI.ev(python_mip_j)
    
    # Compare with 3% tolerance (composition MIP can have more variance)
    assert compare_results(
        python_mip_ev,
        epq_results['sio2_mip'],
        tolerance=0.03
    ), f"SiO2 MIP mismatch: Python={python_mip_ev}, EPQ={epq_results['sio2_mip']}"
